#!/usr/bin/env python
# https://flask.palletsprojects.com/en/stable/quickstart/
# run: $ gunicorn server:app

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict
import flask
import json
import hashlib
import os
import re
import tempfile


THINGS_DIR = Path(__file__).parent / 'things'
THING_ID_PATTERN = re.compile(r'^[0-9a-f]{6}$')

def thing_id_to_path(thing_id):
  if not THING_ID_PATTERN.match(thing_id):
    flask.abort(400, "invalid thing_id.")
  return THINGS_DIR / thing_id

IMGS_DIR = Path(__file__).parent / 'imgs'
IMG_ID_PATTERN = re.compile(r'^[0-9a-f]{40}.[a-z]{3,4}$')
EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

def img_id_to_path(img_id):
  if not IMG_ID_PATTERN.match(img_id):
    flask.abort(400, "invalid img_id.")
  return IMGS_DIR / img_id

app = flask.Flask(
    __name__,
    static_url_path='',
    static_folder='static')

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

@app.post("/imgs")
def serve_imgs_post():
  file = flask.request.files["file"]

  content_type = file.content_type
  ext = EXTENSIONS.get(content_type)
  if not ext:
    flask.abort(400, "unknown content type.")

  sha1 = hashlib.sha1(file.read()).hexdigest()
  name = f"{sha1}.{ext}"
  img_path = IMGS_DIR / name

  if not img_path.exists():
    file.seek(0)
    file.save(img_path)

  return {
    "url": f"/imgs/{name}"
  }

@app.get("/imgs/<img_id>")
def serve_imgs_get(img_id):
  img_path = img_id_to_path(img_id)
  if not img_path.exists():
    flask.abort(404, "img not found.")
  return flask.send_file(img_path)


if __name__ == "__main__":
  app.run(host="0.0.0.0")
