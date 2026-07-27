#!/usr/bin/env python
# https://flask.palletsprojects.com/en/stable/quickstart/
# run: $ gunicorn server:app

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict
import flask
import json
import os
import re
import tempfile
import uuid


THINGS_DIR = Path(__file__).parent / 'things'
THING_ID_PATTERN = re.compile(r'^[0-9a-f]{6}$')

app = flask.Flask(__name__, static_folder='static')

def thing_id_to_path(thing_id):
  if not THING_ID_PATTERN.match(thing_id):
    flask.abort(400, "invalid thing_id.")
  return THINGS_DIR / thing_id

@app.route("/")
def serve_root():
  return "i am a server desu~"

@app.route("/things/<thing_id>", methods=['GET'])
def serve_things_get(thing_id):
  thing_path = thing_id_to_path(thing_id)
  if not thing_path.exists():
    flask.abort(404, "thing not found.")
  return flask.send_file(thing_path, mimetype="application/json")

@app.route("/things/<thing_id>", methods=['POST'])
def serve_things_post(thing_id):
  thing_path = thing_id_to_path(thing_id)
  if not flask.request.headers.get("Content-Type") == "application/json":
    flask.abort(400, "invalid content_type.")
  # TODO enforce max length etc

  raw_body = flask.request.get_data(as_text=True)
  body = json.loads(raw_body)

  new_version = body.get('thing_version')
  if not new_version:
    flask.abort(400, "missing thing_version.")
  new_vesion = int(new_version)

  if thing_path.exists():
    with open(thing_path, 'r') as f:
      existing = json.load(f)
    existing_version = existing['thing_version']
    if new_version <= existing_version:
      flask.abort(400, f"new version {new_version} <= existing version {existing_version}.")

  with tempfile.NamedTemporaryFile(
      dir=THINGS_DIR,
      delete_on_close=False,
      ) as tmp:
    tmp.write(raw_body.encode('utf-8'))
    tmp.close()
    os.replace(tmp.name, thing_path)

  return {'thing_version': new_vesion}


if __name__ == "__main__":
  app.run(host="0.0.0.0")
