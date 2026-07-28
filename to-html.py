#!/usr/bin/env python
from pathlib import Path
import json
import tiptapy

THINGS_DIR = Path(__file__).parent / 'things'

def fix_dict(d):
  for k, v in d.copy().items():
    if k == "alt" and v is None:
      del d[k]
    else:
      fix_json(v)

def fix_list(l):
  for v in l:
    fix_json(v)

def fix_json(j):
  if isinstance(j, dict):
    fix_dict(j)
  elif isinstance(j, list):
    fix_list(j)

def find_title(j):
  for c in j['content']:
    if c['type'] == 'heading':
      return ''.join([v['text'] for v in c['content']])
  return "Untitled"


class Config:
  DOMAIN = "example.org"

renderer = tiptapy.BaseDoc(Config)
path = THINGS_DIR / "123456"
json = json.loads(path.read_text())
fix_json(json)

title = find_title(json)
rendered = renderer.render(json)

print(f"""
<!doctype html>
<html>
<head>
  <title>{title}</title>
</head>
<body>
{rendered}
</body>
</html>
""")
