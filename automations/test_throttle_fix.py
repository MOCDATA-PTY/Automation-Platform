"""
Test the Graph API throttle-handling and large-attachment logic locally.
Uses unittest.mock to simulate Graph API responses without hitting real APIs.
"""
import os
import sys
import json
import base64
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
sys.path.insert(0, os.path.dirname(__file__))

import django
django.setup()

from unittest.mock import patch, MagicMock
from dashboard import views
from dashboard import onedrive_sync

PASS = "\033[92m✔ PASS\033[0m"
FAIL = "\033[91m✘ FAIL\033[0m"
results = []


def test(name):
    """Decorator to register and run a test."""
    def wrapper(fn):
        try:
            fn()
            results.append((name, True, ''))
            print(f"  {PASS}  {name}")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  {FAIL}  {name}  →  {e}")
    return wrapper


print("\n" + "="*70)
print("  THROTTLE & LARGE-ATTACHMENT FIX — LOCAL TESTS")
print("="*70 + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# 1. Test _graph_send_mail with SMALL payload (normal /sendMail path)
# ──────────────────────────────────────────────────────────────────────────────

@test("Small payload sends via /sendMail and returns (True, 202)")
def _():
    mock_resp = MagicMock()
    mock_resp.status_code = 202
    with patch.object(views, 'http_requests') as mock_req:
        mock_req.post.return_value = mock_resp
        payload = {
            'message': {
                'subject': 'Test',
                'body': {'contentType': 'Text', 'content': 'Hello'},
                'toRecipients': [{'emailAddress': {'address': 'test@test.com'}}],
            }
        }
        ok, code = views._graph_send_mail('fake-token', payload)
        assert ok is True, f"Expected True, got {ok}"
        assert code == 202, f"Expected 202, got {code}"


# ──────────────────────────────────────────────────────────────────────────────
# 2. Test _graph_send_mail retries on 429 then succeeds
# ──────────────────────────────────────────────────────────────────────────────

@test("Retries on HTTP 429, then succeeds on second attempt")
def _():
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {'Retry-After': '0'}  # 0s for fast test

    resp_202 = MagicMock()
    resp_202.status_code = 202

    with patch.object(views, 'http_requests') as mock_req:
        mock_req.post.side_effect = [resp_429, resp_202]
        payload = {
            'message': {
                'subject': 'Test',
                'body': {'contentType': 'Text', 'content': 'Hello'},
                'toRecipients': [{'emailAddress': {'address': 'test@test.com'}}],
            }
        }
        ok, code = views._graph_send_mail('fake-token', payload, max_retries=3)
        assert ok is True, f"Expected True, got {ok}"
        assert code == 202, f"Expected 202, got {code}"
        assert mock_req.post.call_count == 2, f"Expected 2 calls, got {mock_req.post.call_count}"


# ──────────────────────────────────────────────────────────────────────────────
# 3. Test _graph_send_mail falls back to draft flow on 413
# ──────────────────────────────────────────────────────────────────────────────

@test("Falls back to draft+upload flow on HTTP 413 (payload too large)")
def _():
    resp_413 = MagicMock()
    resp_413.status_code = 413
    resp_413.headers = {}

    resp_draft = MagicMock()
    resp_draft.status_code = 201
    resp_draft.json.return_value = {'id': 'draft-123'}

    resp_att = MagicMock()
    resp_att.status_code = 201

    resp_send = MagicMock()
    resp_send.status_code = 202

    with patch.object(views, 'http_requests') as mock_req:
        mock_req.post.side_effect = [resp_413, resp_draft, resp_att, resp_send]

        # Small attachment (< 3MB so it goes as direct add to draft)
        small_att = base64.b64encode(b'x' * 1000).decode()
        payload = {
            'message': {
                'subject': 'Test',
                'body': {'contentType': 'Text', 'content': 'Hello'},
                'toRecipients': [{'emailAddress': {'address': 'test@test.com'}}],
                'attachments': [{
                    '@odata.type': '#microsoft.graph.fileAttachment',
                    'name': 'small.pdf',
                    'contentBytes': small_att,
                }],
            }
        }
        ok, code = views._graph_send_mail('fake-token', payload, max_retries=3)
        assert ok is True, f"Expected True, got {ok}"
        assert code == 202, f"Expected 202, got {code}"


# ──────────────────────────────────────────────────────────────────────────────
# 4. Test _graph_send_mail uses draft+upload for large attachments (>3MB base64)
# ──────────────────────────────────────────────────────────────────────────────

@test("Large payload (>3MB base64) auto-uses draft+upload flow")
def _():
    resp_draft = MagicMock()
    resp_draft.status_code = 201
    resp_draft.json.return_value = {'id': 'draft-456'}

    resp_session = MagicMock()
    resp_session.status_code = 200
    resp_session.json.return_value = {'uploadUrl': 'https://fake-upload-url'}

    resp_chunk = MagicMock()
    resp_chunk.status_code = 200

    resp_send = MagicMock()
    resp_send.status_code = 202

    with patch.object(views, 'http_requests') as mock_req:
        mock_req.post.side_effect = [resp_draft, resp_session, resp_send]
        mock_req.put.return_value = resp_chunk

        # Create a >3MB base64 attachment (4MB raw = ~5.3MB base64)
        big_data = base64.b64encode(b'A' * (4 * 1024 * 1024)).decode()
        payload = {
            'message': {
                'subject': 'Big Email',
                'body': {'contentType': 'HTML', 'content': '<p>Big</p>'},
                'toRecipients': [{'emailAddress': {'address': 'test@test.com'}}],
                'attachments': [{
                    '@odata.type': '#microsoft.graph.fileAttachment',
                    'name': 'report.pdf',
                    'contentBytes': big_data,
                }],
            }
        }
        ok, code = views._graph_send_mail('fake-token', payload, max_retries=3)
        assert ok is True, f"Expected True, got {ok}"
        assert code == 202, f"Expected 202, got {code}"
        # Should have used PUT for chunk upload
        assert mock_req.put.call_count >= 1, f"Expected PUT calls for chunks, got {mock_req.put.call_count}"


# ──────────────────────────────────────────────────────────────────────────────
# 5. Test _graph_send_mail handles token expiry (401 → refresh → retry)
# ──────────────────────────────────────────────────────────────────────────────

@test("Handles HTTP 401 by refreshing token and retrying")
def _():
    resp_401 = MagicMock()
    resp_401.status_code = 401
    resp_401.headers = {}

    resp_202 = MagicMock()
    resp_202.status_code = 202

    with patch.object(views, 'http_requests') as mock_req, \
         patch.object(views, '_get_graph_token', return_value='new-token'):
        mock_req.post.side_effect = [resp_401, resp_202]
        payload = {
            'message': {
                'subject': 'Test',
                'body': {'contentType': 'Text', 'content': 'Hello'},
                'toRecipients': [{'emailAddress': {'address': 'test@test.com'}}],
            }
        }
        ok, code = views._graph_send_mail('expired-token', payload, max_retries=3)
        assert ok is True, f"Expected True, got {ok}"


# ──────────────────────────────────────────────────────────────────────────────
# 6. Test download_file retries on 429
# ──────────────────────────────────────────────────────────────────────────────

@test("download_file retries on HTTP 429 then returns content")
def _():
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {'Retry-After': '0'}

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.content = b'file-content-here'

    with patch.object(onedrive_sync, 'get_access_token', return_value='fake-token'), \
         patch.object(onedrive_sync.requests, 'get') as mock_get:
        mock_get.side_effect = [resp_429, resp_200]
        result = onedrive_sync.download_file('file-id-123')
        assert result is not None, "Expected file content, got None"
        assert result.read() == b'file-content-here', "Content mismatch"
        assert mock_get.call_count == 2, f"Expected 2 attempts, got {mock_get.call_count}"


# ──────────────────────────────────────────────────────────────────────────────
# 7. Test download_file retries on 503
# ──────────────────────────────────────────────────────────────────────────────

@test("download_file retries on HTTP 503 (service unavailable)")
def _():
    resp_503 = MagicMock()
    resp_503.status_code = 503
    resp_503.headers = {'Retry-After': '0'}

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.content = b'recovered'

    with patch.object(onedrive_sync, 'get_access_token', return_value='fake-token'), \
         patch.object(onedrive_sync.requests, 'get') as mock_get:
        mock_get.side_effect = [resp_503, resp_503, resp_200]
        result = onedrive_sync.download_file('file-xyz')
        assert result is not None, "Expected content after retry"
        assert result.read() == b'recovered'


# ──────────────────────────────────────────────────────────────────────────────
# 8. Test download_file returns None after all retries exhausted
# ──────────────────────────────────────────────────────────────────────────────

@test("download_file returns None after 5 failed attempts")
def _():
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {'Retry-After': '0'}

    with patch.object(onedrive_sync, 'get_access_token', return_value='fake-token'), \
         patch.object(onedrive_sync.requests, 'get') as mock_get:
        mock_get.return_value = resp_429
        result = onedrive_sync.download_file('always-throttled')
        assert result is None, f"Expected None, got {result}"
        assert mock_get.call_count == 5, f"Expected 5 attempts, got {mock_get.call_count}"


# ──────────────────────────────────────────────────────────────────────────────
# 9. Verify bulk send uses 2 threads (not 5)
# ──────────────────────────────────────────────────────────────────────────────

@test("Bulk send_all_touchpoint uses max_workers=2")
def _():
    import inspect
    source = inspect.getsource(views.send_all_touchpoint)
    assert 'max_workers=2' in source, "Expected max_workers=2 in send_all_touchpoint"
    assert 'max_workers=5' not in source, "Should NOT have max_workers=5 anymore"


# ──────────────────────────────────────────────────────────────────────────────
# 10. Verify throttle starts at 3.0s (not 1.0s)
# ──────────────────────────────────────────────────────────────────────────────

@test("Bulk send throttle starts at 3.0s for large payloads")
def _():
    import inspect
    source = inspect.getsource(views.send_all_touchpoint)
    assert '_throttle = [3.0]' in source, "Expected _throttle = [3.0] in send_all_touchpoint"


# ──────────────────────────────────────────────────────────────────────────────
# 11. Verify send_touchpoint uses _graph_send_mail (not raw post)
# ──────────────────────────────────────────────────────────────────────────────

@test("send_touchpoint uses _graph_send_mail instead of raw post")
def _():
    import inspect
    source = inspect.getsource(views.send_touchpoint)
    assert '_graph_send_mail' in source, "send_touchpoint should call _graph_send_mail"
    assert 'http_requests.post' not in source, "send_touchpoint should NOT use raw http_requests.post"


# ──────────────────────────────────────────────────────────────────────────────
# 12. Size calculation test — 7MB raw → must trigger draft flow
# ──────────────────────────────────────────────────────────────────────────────

@test("7MB attachment (base64) triggers draft+upload flow, not /sendMail")
def _():
    # 5MB raw file → ~6.67MB base64 string → above 3MB threshold
    raw_5mb = b'B' * (5 * 1024 * 1024)
    b64_data = base64.b64encode(raw_5mb).decode()

    resp_draft = MagicMock()
    resp_draft.status_code = 201
    resp_draft.json.return_value = {'id': 'draft-7mb'}

    resp_session = MagicMock()
    resp_session.status_code = 200
    resp_session.json.return_value = {'uploadUrl': 'https://upload.example.com'}

    resp_chunk = MagicMock()
    resp_chunk.status_code = 200

    resp_send = MagicMock()
    resp_send.status_code = 202

    with patch.object(views, 'http_requests') as mock_req:
        mock_req.post.side_effect = [resp_draft, resp_session, resp_send]
        mock_req.put.return_value = resp_chunk

        payload = {
            'message': {
                'subject': '7MB Email',
                'body': {'contentType': 'HTML', 'content': '<p>Large</p>'},
                'toRecipients': [{'emailAddress': {'address': 'user@test.com'}}],
                'attachments': [
                    {
                        '@odata.type': '#microsoft.graph.fileAttachment',
                        'name': 'report.pdf',
                        'contentBytes': b64_data,
                    },
                    {
                        '@odata.type': '#microsoft.graph.fileAttachment',
                        'name': 'sig.png',
                        'contentBytes': base64.b64encode(b'P' * 500000).decode(),
                        'isInline': True,
                        'contentId': 'sig',
                    },
                ],
            }
        }
        ok, code = views._graph_send_mail('token', payload)
        assert ok is True, f"Expected True, got {ok}"
        # Should NOT have called /sendMail — went straight to draft flow
        first_call_url = mock_req.post.call_args_list[0][0][0]
        assert '/messages' in first_call_url, f"First call should be /messages (draft), got {first_call_url}"
        assert '/sendMail' not in first_call_url, "Should NOT use /sendMail for large payloads"


# ──────────────────────────────────────────────────────────────────────────────
#  SUMMARY
# ──────────────────────────────────────────────────────────────────────────────

print("\n" + "="*70)
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
print(f"  RESULTS:  {passed} passed,  {failed} failed,  {len(results)} total")
if failed:
    print("\n  FAILURES:")
    for name, ok, err in results:
        if not ok:
            print(f"    ✘ {name}")
            print(f"      {err}")
print("="*70 + "\n")

sys.exit(0 if failed == 0 else 1)
