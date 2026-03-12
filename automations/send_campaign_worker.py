#!/usr/bin/env python3
"""
Standalone campaign worker — launched as a subprocess by the web UI
so the email campaign survives gunicorn restarts.

Usage:
    python send_campaign_worker.py --tp-num 1 --job-id tp1_1234567890
"""
import os
import sys
import argparse
import time
import json
import base64
import re
import threading
import tempfile
import concurrent.futures

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
import django
django.setup()

from datetime import datetime
from django.conf import settings as django_settings
import requests as http_requests

from dashboard.models import USEUContact, TouchpointTemplate
from dashboard.views import _get_graph_token, GRAPH_MAILBOX, update_touchpoint_progress


def _write_job_file(job_file, data):
    """Atomically write job progress to file."""
    dir_name = os.path.dirname(job_file)
    fd, tmp = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f)
        os.replace(tmp, job_file)
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass


def run_campaign(tp_num, job_id, job_file):
    tp_sent_field = f'tp{tp_num}_sent_on'
    tp_type = f'tp{tp_num}'

    # Find eligible contacts
    filters = {'status': 'Active', tp_sent_field: ''}
    contacts = list(
        USEUContact.objects.filter(**filters)
        .exclude(email='').exclude(email__isnull=True)
    )
    total = len(contacts)
    print(f"[WORKER] TP{tp_num}: {total} eligible contacts", flush=True)

    if not contacts:
        _write_job_file(job_file, {'total': 0, 'sent': 0, 'failed': 0, 'current': '', 'done': True, 'results': []})
        update_touchpoint_progress(tp_type, total=0, sent=0, failed=0, status='idle')
        return

    # Get template
    try:
        template = TouchpointTemplate.objects.get(touchpoint_number=tp_num)
    except TouchpointTemplate.DoesNotExist:
        print(f"[WORKER] Template TP{tp_num} not found", flush=True)
        _write_job_file(job_file, {'total': total, 'sent': 0, 'failed': 0, 'current': 'Error: template not found', 'done': True, 'results': []})
        update_touchpoint_progress(tp_type, status='idle')
        return

    # Seed progress file so the UI can poll immediately
    _write_job_file(job_file, {'total': total, 'sent': 0, 'failed': 0, 'current': '', 'done': False, 'results': []})
    update_touchpoint_progress(tp_type, total=total, sent=0, failed=0, status='sending')

    # Get token
    token = _get_graph_token()
    if not token:
        print("[WORKER] Failed to get Graph API token", flush=True)
        _write_job_file(job_file, {'total': total, 'sent': 0, 'failed': 0, 'current': 'Error: authentication failed', 'done': True, 'results': []})
        update_touchpoint_progress(tp_type, status='idle')
        return

    # Token auto-refresh (tokens expire after 1 hour, refresh at 45 min)
    token_lock = threading.Lock()
    token_data = {'value': token, 'obtained': time.time()}

    def _fresh_token():
        with token_lock:
            if time.time() - token_data['obtained'] > 2700:
                new_tok = _get_graph_token()
                if new_tok:
                    token_data['value'] = new_tok
                    token_data['obtained'] = time.time()
            return token_data['value']

    # Build template body and attachments once (shared across all sends)
    body_content = template.body_html if template.body_html else template.body
    content_type = 'HTML' if template.body_html else 'Text'

    sig_inline = None
    if content_type == 'HTML':
        body_content = re.sub(
            r'https://drive\.google\.com/thumbnail\?id=[^"\'&]+(?:&amp;[^"\']*|&[^"\']*)*',
            r'cid:signature_waldo',
            body_content,
            flags=re.IGNORECASE
        )
        sig_path = os.path.join(django_settings.BASE_DIR, 'static', 'signature_waldo.png')
        if os.path.isfile(sig_path):
            with open(sig_path, 'rb') as sf:
                sig_inline = {
                    '@odata.type': '#microsoft.graph.fileAttachment',
                    'name': 'signature_waldo.png',
                    'contentType': 'image/png',
                    'contentBytes': base64.b64encode(sf.read()).decode('utf-8'),
                    'contentId': 'signature_waldo',
                    'isInline': True,
                }

    att_data = None
    if template.attachment:
        try:
            att_path = template.attachment.path
            with open(att_path, 'rb') as f:
                att_bytes = f.read()
            raw_name = os.path.basename(att_path)
            name_part, ext = os.path.splitext(raw_name)
            att_name = name_part.replace('_', ' ').replace('-', ' ')
            att_name = ' '.join(att_name.split()) + ext
            att_data = {
                '@odata.type': '#microsoft.graph.fileAttachment',
                'name': att_name,
                'contentBytes': base64.b64encode(att_bytes).decode('utf-8'),
            }
        except Exception as e:
            print(f"[WORKER] Attachment error: {e}", flush=True)

    now_str = datetime.now().strftime('%d/%m/%Y')
    _progress_lock = threading.Lock()
    _throttle = [3.0]
    state = {'sent': 0, 'failed': 0}

    def _send_one(contact):
        try:
            email_addr = contact.email.strip()
            if not email_addr:
                return

            time.sleep(_throttle[0])

            with _progress_lock:
                _write_job_file(job_file, {
                    'total': total,
                    'sent': state['sent'],
                    'failed': state['failed'],
                    'current': email_addr,
                    'done': False,
                    'results': [],
                })
            update_touchpoint_progress(tp_type, current_email=email_addr)

            final_body = body_content
            final_body = final_body.replace('{{org_name}}', contact.org_name or '')
            final_body = final_body.replace('{{contact_name}}', contact.contact_name or '')
            final_body = final_body.replace('{{email}}', contact.email or '')
            final_body = final_body.replace('{{phone}}', contact.phone or '')
            final_body = final_body.replace('{{touchpoint_number}}', str(tp_num))

            subject = template.subject or ''
            subject = subject.replace('{{org_name}}', contact.org_name or '')
            subject = subject.replace('{{contact_name}}', contact.contact_name or '')

            current_token = _fresh_token()
            payload = {
                'message': {
                    'subject': subject,
                    'body': {'contentType': content_type, 'content': final_body},
                    'from': {'emailAddress': {'name': 'Magnum Opus Consultants', 'address': GRAPH_MAILBOX}},
                    'toRecipients': [{'emailAddress': {'address': email_addr}}],
                },
                'saveToSentItems': True,
            }
            att_list = []
            if att_data:
                att_list.append(att_data)
            if sig_inline:
                att_list.append(sig_inline)
            if att_list:
                payload['message']['attachments'] = att_list

            print(f"[WORKER] Sending to: {email_addr}", flush=True)
            sent_ok = False
            _status = 0

            for attempt in range(5):
                try:
                    headers = {'Authorization': f'Bearer {current_token}', 'Content-Type': 'application/json'}
                    r = http_requests.post(
                        f'https://graph.microsoft.com/v1.0/users/{GRAPH_MAILBOX}/sendMail',
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    _status = r.status_code
                    if _status == 202:
                        sent_ok = True
                        break
                    elif _status == 429:
                        retry_after = int(r.headers.get('Retry-After', 10))
                        print(f"[WORKER] 429 rate limit, waiting {retry_after}s", flush=True)
                        time.sleep(retry_after + attempt * 5)
                    else:
                        print(f"[WORKER] HTTP {_status} for {email_addr}: {r.text[:200]}", flush=True)
                        break
                except Exception as e:
                    print(f"[WORKER] Request error for {email_addr}: {e}", flush=True)
                    _status = 0
                    time.sleep(3 * (attempt + 1))

            if sent_ok:
                _throttle[0] = max(_throttle[0] * 0.95, 1.5)

            with _progress_lock:
                if sent_ok or _status in [400, 404, 422]:
                    state['sent'] += 1
                    setattr(contact, tp_sent_field, now_str)
                    contact.last_touch = str(tp_num)
                    contact.save(update_fields=[tp_sent_field, 'last_touch'])
                    update_touchpoint_progress(tp_type, sent=state['sent'])
                else:
                    state['failed'] += 1
                    update_touchpoint_progress(tp_type, failed=state['failed'])

        except Exception as e:
            print(f"[WORKER] Unhandled exception for {getattr(contact, 'email', '?')}: {e}", flush=True)
            with _progress_lock:
                state['failed'] += 1

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            pool.map(_send_one, contacts)
    except Exception as e:
        print(f"[WORKER] Executor error: {e}", flush=True)
    finally:
        _write_job_file(job_file, {
            'total': total,
            'sent': state['sent'],
            'failed': state['failed'],
            'current': '',
            'done': True,
            'results': [],
        })
        update_touchpoint_progress(tp_type, status='idle')
        print(f"[WORKER] Complete — sent: {state['sent']}, failed: {state['failed']}", flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tp-num', type=int, required=True)
    parser.add_argument('--job-id', type=str, required=True)
    args = parser.parse_args()

    job_file = os.path.join(project_root, f'send_job_{args.job_id}.json')
    run_campaign(args.tp_num, args.job_id, job_file)
