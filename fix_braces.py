import re

with open('frontend_skepticai/src/services/apiService.ts', 'r') as f:
    content = f.read()

# Find the problematic section
old = '\n}\n\n}\n\n}\n\nfunction getApiBaseUrl(): string {'
new = '\nfunction getApiBaseUrl(): string {'

if old in content:
    content = content.replace(old, new)
    with open('frontend_skepticai/src/services/apiService.ts', 'w') as f:
        f.write(content)
    print('Fixed!')
else:
    # Try alternative patterns
    print('Trying alternative patterns...')
    # Look for the exact pattern
    matches = list(re.finditer(r'\}\n\n\}\n\n\}\n\nfunction getApiBaseUrl', content))
    print('Matches:', matches)
    for match in re.finditer(r'\}\n\n\}\n\n\}', content):
        print(f'Match at {match.start()}-{match.end()}: {repr(content[match.start():match.end()])}')