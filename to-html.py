#!/usr/bin/env python
from pathlib import Path
import json
import tiptapy

import db_storage

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

class Config:
  DOMAIN = "example.org"

renderer = tiptapy.BaseDoc(Config)

store = db_storage.DbStorage()
doc = store.thing_get("1")
doc = json.loads(doc.data)
store.close()

fix_json(doc)

title = doc['thing_title']
rendered = renderer.render(doc)

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
