from pathlib import Path
import flask
import hashlib
import json
import os
import re
import tempfile


THINGS_DIR = Path(__file__).parent / 'things'
THING_ID_PATTERN = re.compile(r'^[0-9a-f]{6}$')

IMGS_DIR = Path(__file__).parent / 'imgs'
IMG_ID_PATTERN = re.compile(r'^[0-9a-f]{40}.[a-z]{3,4}$')


class FsStorage:

  def __init__(self):
    THINGS_DIR.mkdir(exist_ok=True)
    IMGS_DIR.mkdir(exist_ok=True)

  def thing_id_to_path(self, thing_id):
    if not THING_ID_PATTERN.match(thing_id):
      flask.abort(400, "invalid thing_id.")
    return THINGS_DIR / thing_id

  def thing_get(self, thing_id):
    thing_path = self.thing_id_to_path(thing_id)
    if not thing_path.exists():
      flask.abort(404, "thing not found.")
    return flask.send_file(thing_path, mimetype="application/json")

  def thing_write_update(self, thing_id, new_version, new_body):
    thing_path = self.thing_id_to_path(thing_id)
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
      tmp.write(new_body.encode('utf-8'))
      tmp.close()
      os.replace(tmp.name, thing_path)

  def img_id_to_path(self, img_id):
    if not IMG_ID_PATTERN.match(img_id):
      flask.abort(400, "invalid img_id.")
    return IMGS_DIR / img_id

  def img_get(self, img_id):
    img_path = self.img_id_to_path(img_id)
    if not img_path.exists():
      flask.abort(404, "img not found.")
    return flask.send_file(img_path)

  def img_write_new(self, file, content_type, extension):
    sha1 = hashlib.sha1(file.read()).hexdigest()
    img_id = f"{sha1}.{extension}"
    img_path = IMGS_DIR / img_id

    if not img_path.exists():
      file.seek(0)
      file.save(img_path)

    return img_id
