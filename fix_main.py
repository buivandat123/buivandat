#!/usr/bin/env python3
import os
import re

main_file = "/sdcard/download/kryzis/main.py"

with open(main_file, "r", encoding="utf-8") as f:
    content = f.read()

# Tìm dòng super().__init__ và thay thế đúng indent
pattern = r'(\s+)super\(\)\.__init__\(api_key, secret_key, imei, session_cookies\)'

def replacer(match):
    indent = match.group(1)
    return f'''{indent}try:
{indent}    super().__init__(api_key, secret_key, imei, session_cookies)
{indent}except Exception as e:
{indent}    if "Phone and password not set" in str(e):
{indent}        print("[MainBot] ⚠️ Login skipped, using session cookies")
{indent}        self._imei = imei
{indent}        self.imei = imei
{indent}        self.session_cookies = session_cookies
{indent}    else:
{indent}        raise'''

new_content = re.sub(pattern, replacer, content, flags=re.DOTALL)

if new_content != content:
    with open(main_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("✅ Đã patch main.py thành công!")
else:
    print("⚠️ Không tìm thấy dòng cần sửa")
