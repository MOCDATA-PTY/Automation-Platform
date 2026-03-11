import re

test_html = '''<img src="https://drive.google.com/thumbnail?id=1MGfpWvjmlr2gXLFo-Zx8NBs8fO5Svnq7&amp;sz=w600" alt="Waldo Signature">'''

print("Original:")
print(test_html)
print()

result = re.sub(
    r'https://drive\.google\.com/thumbnail\?id=[^"\'&]+(?:&amp;[^"\']*|&[^"\']*)*',
    r'https://workspace.moc-pty.com/static/signature_waldo.png',
    test_html,
    flags=re.IGNORECASE
)
print("After regex:")
print(result)
print()

# Check if the static image is accessible
import requests
r = requests.head('https://workspace.moc-pty.com/static/signature_waldo.png', timeout=10)
print(f"Static image check: {r.status_code} {r.headers.get('Content-Type', 'unknown')}")
