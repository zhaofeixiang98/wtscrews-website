#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

# Suppress deprecation warnings
os.environ['PYTHONWARNINGS'] = 'ignore'

# Print headers immediately
print("Content-Type: text/html")
print("Location: http://38.60.251.149/pags/success.html")
print()

# Parse form data
query_string = os.environ.get('QUERY_STRING', '')
if query_string:
    from urllib.parse import parse_qs
    data = parse_qs(query_string)
    # Get first value for each field
    name = data.get('name', [''])[0]
    email = data.get('email', [''])[0]
    company = data.get('company', [''])[0]
    phone = data.get('phone', [''])[0]
    subject = data.get('subject', [''])[0]
    message = data.get('message', [''])[0]
else:
    # Read from stdin for POST requests
    content_length = int(os.environ.get('CONTENT_LENGTH', 0))
    if content_length > 0:
        post_data = sys.stdin.read(content_length)
        from urllib.parse import parse_qs
        data = parse_qs(post_data)
        name = data.get('name', [''])[0]
        email = data.get('email', [''])[0]
        company = data.get('company', [''])[0]
        phone = data.get('phone', [''])[0]
        subject = data.get('subject', [''])[0]
        message = data.get('message', [''])[0]
    else:
        name = email = company = phone = subject = message = ''

# Get client IP
client_ip = os.environ.get('REMOTE_ADDR', '127.0.0.1')

# Save to file
import json
from time import time

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
save_dir = os.path.join(project_root, 'users')
os.makedirs(save_dir, exist_ok=True)

# Throttle check
throttle_file = os.path.join(save_dir, '.last_submits.json')
last_submits = {}
try:
    if os.path.exists(throttle_file):
        with open(throttle_file, 'r') as f:
            last_submits = json.load(f)
except:
    pass

now_ts = time()
key_ip = f"ip:{client_ip}"
key_email = f"email:{email.lower()}"

if now_ts - float(last_submits.get(key_ip, 0)) < 30 or (email and now_ts - float(last_submits.get(key_email, 0)) < 30):
    print("<html><head><meta charset='utf-8'><title>Too Many Requests</title></head><body>")
    print("<h2>Please wait 30 seconds before submitting again.</h2>")
    print("<p><a href='/pags/contact.html'>Back to Contact</a></p>")
    print("</body></html>")
    sys.exit(0)

# Save data
record = {
    'name': name,
    'email': email,
    'company': company,
    'phone': phone,
    'subject': subject,
    'message': message,
    'ip': client_ip,
    'time': datetime.now(timezone.utc).isoformat()
}

safe_email = email.replace('@', '_at_').replace('.', '_') if email else 'noemail'
safe_time = datetime.now(timezone.utc).isoformat().replace(':', '-')
filename = os.path.join(save_dir, f"{safe_time}_{safe_email}.json")

with open(filename, 'w', encoding='utf-8') as f:
    json.dump(record, f, ensure_ascii=False, indent=2)

# Update throttle
last_submits[key_ip] = now_ts
if email:
    last_submits[key_email] = now_ts
try:
    with open(throttle_file, 'w') as f:
        json.dump(last_submits, f)
except:
    pass

# HTML fallback (will be overridden by redirect)
print("<html><head>")
print("<meta http-equiv='refresh' content='0;url=/pags/success.html'>")
print("</head><body>")
print("<p>Redirecting...</p>")
print("</body></html>")
