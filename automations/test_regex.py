import re
test = 'src="https://drive.google.com/thumbnail?id=1MGfpWvjmlr2gXLFo-Zx8NBs8fO5Svnq7&amp;sz=w600"'
result = re.sub(
    r"""https://drive\.google\.com/thumbnail\?id=[^"'&]+(?:&amp;[^"']*|&[^"']*)*""",
    'https://workspace.moc-pty.com/static/signature_waldo.png',
    test,
    flags=re.IGNORECASE
)
print('Before:', test)
print('After:', result)
print('Changed:', test != result)
