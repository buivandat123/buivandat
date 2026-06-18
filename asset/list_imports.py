import os
import re

imports = set()
for root, _, files in os.walk('.'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    for line in fh:
                        line = line.strip()
                        m = re.match(r'^(?:from|import)\s+([\w_\.]+)', line)
                        if m:
                            imports.add(m.group(1).split('.')[0])
            except Exception:
                continue
for name in sorted(imports):
    print(name)
