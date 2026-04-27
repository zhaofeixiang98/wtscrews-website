#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, re
import email.parser
from admin_auth import is_request_authenticated

sys.stdout.write("Content-Type: application/json; charset=utf-8\r\n\r\n")
sys.stdout.flush()

def respond(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.flush()
    sys.exit(0)


if not is_request_authenticated():
    respond({'success': False, 'error': 'unauthorized'})

try:
    content_type   = os.environ.get('CONTENT_TYPE', '')
    content_length = int(os.environ.get('CONTENT_LENGTH', 0) or 0)
    raw = sys.stdin.buffer.read(content_length)

    # Parse multipart using email module (no deprecated cgi module)
    msg = email.parser.BytesParser().parsebytes(
        b'Content-Type: ' + content_type.encode() + b'\r\n\r\n' + raw
    )

    file_field  = None   # {'filename': str, 'data': bytes}
    rename_raw  = ''

    for part in msg.get_payload():
        disp = str(part.get('Content-Disposition', ''))  # Header obj → str
        name_m  = re.search(r'name="([^"]+)"',     disp)
        fname_m = re.search(r'filename="([^"]*)"', disp)
        if not name_m:
            continue
        name = name_m.group(1)

        if name == 'file' and fname_m:
            file_field = {
                'filename': fname_m.group(1),
                'data':     part.get_payload(decode=True),
            }
        elif name == 'rename':
            rename_raw = (part.get_payload(decode=True) or b'').decode('utf-8', errors='replace').strip()

except Exception as e:
    respond({'success': False, 'error': 'Parse error: ' + str(e)})

if not file_field or not file_field.get('filename'):
    respond({'success': False, 'error': '未选择文件'})

original = os.path.basename(file_field['filename'])
ext = os.path.splitext(original)[1].lower()
if ext not in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}:
    respond({'success': False, 'error': '仅支持 jpg/png/gif/webp/svg 格式'})

if rename_raw:
    safe_base  = re.sub(r'[^a-zA-Z0-9_\-]', '-', os.path.splitext(rename_raw)[0]).strip('-') or 'image'
    final_name = safe_base + ext
else:
    final_name = re.sub(r'[^a-zA-Z0-9_\-.]', '-', original)
    final_name = re.sub(r'-{2,}', '-', final_name).strip('-') or ('image' + ext)

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir   = os.path.abspath(os.path.join(script_dir, '..'))
upload_dir = os.path.join(base_dir, 'images', 'news')

try:
    os.makedirs(upload_dir, exist_ok=True)

    base_name = os.path.splitext(final_name)[0]
    candidate = final_name
    counter   = 1
    while os.path.exists(os.path.join(upload_dir, candidate)):
        candidate = f'{base_name}-{counter}{ext}'
        counter  += 1
    final_name = candidate

    with open(os.path.join(upload_dir, final_name), 'wb') as f:
        f.write(file_field['data'])

    rel_path = 'news/' + final_name
    respond({
        'success': True,
        'filename': final_name,
        'path': rel_path,
        'admin_path': '../../images/' + rel_path,
        'url': '/images/' + rel_path,
    })
except Exception as e:
    respond({'success': False, 'error': '保存失败: ' + str(e)})
