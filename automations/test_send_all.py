"""
Test the send_all_touchpoint logic — verifies sending works,
progress updates, errors are handled, and cancel works.
Mocks the Graph API so no real emails are sent.
"""
import os, sys, json, time, threading
from unittest.mock import patch, MagicMock

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from dashboard.models import USEUContact, TouchpointTemplate
from dashboard import views


def mock_response(status=202, headers=None, text='OK'):
    r = MagicMock()
    r.status_code = status
    r.headers = headers or {}
    r.text = text
    return r


def setup(n=5):
    tpl, _ = TouchpointTemplate.objects.get_or_create(
        touchpoint_number=1,
        defaults={'subject': 'Test {{org_name}}', 'body': 'Hi', 'body_html': '<p>Hi</p>'}
    )
    ids = []
    for i in range(n):
        c = USEUContact.objects.create(
            org_name=f'TESTORG_{i}', contact_name=f'Person {i}',
            email=f'test_{i}_{int(time.time()*1000)}@example.com',
            status='Active', tp1_sent_on=''
        )
        ids.append(c.id)
    return ids, tpl


def cleanup(ids):
    USEUContact.objects.filter(id__in=ids).delete()


def get_user():
    u = User.objects.first()
    if not u:
        u = User.objects.create_user('testuser', 'test@test.com', 'pass')
    return u


def start_job(user):
    factory = RequestFactory()
    req = factory.post('/useu/send-all/', data=json.dumps({'touchpoint_number': 1}),
                       content_type='application/json')
    req.user = user
    resp = views.send_all_touchpoint(req)
    return json.loads(resp.content)


def wait_done(job_id, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        prog = views._send_all_progress.get(job_id)
        if prog and prog['done']:
            return prog
        time.sleep(0.1)
    return views._send_all_progress.get(job_id)


def test_basic():
    print('\n' + '='*50)
    print('TEST 1: Basic send - 5 contacts, all succeed')
    print('='*50)
    ids, _ = setup(5)
    try:
        user = get_user()
        with patch('dashboard.views.http_requests.post', return_value=mock_response(202)), \
             patch('dashboard.views._get_graph_token', return_value='fake'):
            data = start_job(user)
            assert data['ok'], f'Start failed: {data}'
            prog = wait_done(data['job_id'])
            assert prog['done'], 'Not done!'
            assert prog['sent'] >= 5, f'Only sent {prog["sent"]}'
            assert prog['failed'] == 0, f'Had {prog["failed"]} failures'
            for cid in ids:
                c = USEUContact.objects.get(id=cid)
                assert c.tp1_sent_on != '', f'Contact {cid} not updated'
            print(f'  PASS - sent={prog["sent"]} failed={prog["failed"]}')
            return True
    finally:
        cleanup(ids)


def test_api_error():
    print('\n' + '='*50)
    print('TEST 2: API returns 500 - should fail fast, not hang')
    print('='*50)
    ids, _ = setup(3)
    try:
        user = get_user()
        with patch('dashboard.views.http_requests.post',
                   return_value=mock_response(500, text='Internal Server Error')), \
             patch('dashboard.views._get_graph_token', return_value='fake'):
            data = start_job(user)
            start = time.time()
            prog = wait_done(data['job_id'], timeout=15)
            elapsed = time.time() - start
            assert prog['done'], f'Not done after {elapsed:.1f}s!'
            assert prog['sent'] == 0
            assert prog['failed'] >= 3
            assert prog['last_error'] != '', f'No error message!'
            print(f'  PASS - failed fast in {elapsed:.1f}s, error: {prog["last_error"][:80]}')
            return True
    finally:
        cleanup(ids)


def test_429_retry():
    print('\n' + '='*50)
    print('TEST 3: API returns 429 then 202 - should retry and succeed')
    print('='*50)
    ids, _ = setup(3)
    try:
        user = get_user()
        call_n = [0]
        def mock_post(*a, **k):
            call_n[0] += 1
            if call_n[0] % 2 == 1:
                return mock_response(429, headers={'Retry-After': '1'})
            return mock_response(202)

        with patch('dashboard.views.http_requests.post', side_effect=mock_post), \
             patch('dashboard.views._get_graph_token', return_value='fake'):
            data = start_job(user)
            prog = wait_done(data['job_id'], timeout=30)
            assert prog['done']
            assert prog['sent'] >= 3, f'Only sent {prog["sent"]}'
            print(f'  PASS - all sent after retries, API calls={call_n[0]}')
            return True
    finally:
        cleanup(ids)


def test_timeout():
    print('\n' + '='*50)
    print('TEST 4: API times out - should not hang forever')
    print('='*50)
    ids, _ = setup(2)
    try:
        user = get_user()
        import requests as real_requests
        def mock_post(*a, **k):
            raise real_requests.exceptions.Timeout('Connection timed out')

        with patch('dashboard.views.http_requests.post', side_effect=mock_post), \
             patch('dashboard.views._get_graph_token', return_value='fake'):
            data = start_job(user)
            start = time.time()
            prog = wait_done(data['job_id'], timeout=30)
            elapsed = time.time() - start
            assert prog['done'], f'Not done after {elapsed:.1f}s!'
            assert prog['failed'] >= 2
            assert 'Timeout' in prog.get('last_error', ''), f'No timeout error: {prog.get("last_error")}'
            print(f'  PASS - handled timeout in {elapsed:.1f}s, error: {prog["last_error"][:80]}')
            return True
    finally:
        cleanup(ids)


def test_cancel():
    print('\n' + '='*50)
    print('TEST 5: Cancel mid-send - should stop and mark done')
    print('='*50)
    ids, _ = setup(20)
    try:
        user = get_user()
        call_n = [0]
        def slow_post(*a, **k):
            call_n[0] += 1
            time.sleep(0.1)
            return mock_response(202)

        with patch('dashboard.views.http_requests.post', side_effect=slow_post), \
             patch('dashboard.views._get_graph_token', return_value='fake'):
            data = start_job(user)
            job_id = data['job_id']
            time.sleep(1)
            views._send_all_progress[job_id]['cancel'] = True
            prog = wait_done(job_id, timeout=10)
            assert prog['done'], 'Not done after cancel!'
            assert prog['sent'] < 20, f'Sent all {prog["sent"]} - cancel didnt work'
            assert 'Cancel' in prog.get('last_error', ''), f'No cancel message'
            print(f'  PASS - cancelled after {prog["sent"]} sent, {prog["failed"]} failed')
            return True
    finally:
        cleanup(ids)


def test_token_fail():
    print('\n' + '='*50)
    print('TEST 6: Token failure - should immediately mark done')
    print('='*50)
    ids, _ = setup(2)
    try:
        user = get_user()
        with patch('dashboard.views._get_graph_token', return_value=None):
            data = start_job(user)
            prog = wait_done(data['job_id'], timeout=5)
            assert prog['done']
            assert 'token' in prog.get('last_error', '').lower() or 'Token' in prog.get('last_error', '')
            print(f'  PASS - token failure handled: {prog.get("last_error")}')
            return True
    finally:
        cleanup(ids)


if __name__ == '__main__':
    print('='*50)
    print('SEND ALL - TEST SUITE')
    print('='*50)

    tests = [
        ('basic_send', test_basic),
        ('api_500_error', test_api_error),
        ('429_retry', test_429_retry),
        ('timeout', test_timeout),
        ('cancel', test_cancel),
        ('token_failure', test_token_fail),
    ]

    results = {}
    for name, fn in tests:
        try:
            ok = fn()
            results[name] = 'PASS' if ok else 'FAIL'
        except Exception as e:
            results[name] = f'ERROR: {e}'
            import traceback; traceback.print_exc()

    print('\n' + '='*50)
    print('SUMMARY:')
    for k, v in results.items():
        print(f'  {k}: {v}')

    passed = sum(1 for v in results.values() if v == 'PASS')
    total = len(results)
    print(f'\n{passed}/{total} passed')
    sys.exit(0 if passed == total else 1)
