#!/usr/bin/env python
from pathlib import Path
import tiptapy

THINGS_DIR = Path(__file__).parent / 'things'

class Config:
  DOMAIN = "example.org"

renderer = tiptapy.BaseDoc(Config)
path = THINGS_DIR / "123456"
out = renderer.render(path.read_text())
print(out)
