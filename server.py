#!/usr/bin/env python
# https://flask.palletsprojects.com/en/stable/quickstart/
# run: $ gunicorn server:app

import flask
import json

import fs_storage


EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

store = fs_storage.FsStorage()

app = flask.Flask(
    __name__,
    static_url_path='',
    static_folder='static')

@app.route("/")
def serve_root():
  return "i am a server desu~"

@app.get("/things/<thing_id>")
def serve_things_get(thing_id):
  return store.thing_get(thing_id)

@app.post("/things/<thing_id>")
def serve_things_post(thing_id):
  if not flask.request.headers.get("Content-Type") == "application/json":
    flask.abort(400, "invalid content_type.")
  # TODO enforce max length etc
  # TODO validate thing_version, thing_date

  raw_body = flask.request.get_data(as_text=True)
  body = json.loads(raw_body)

  new_version = body.get('thing_version')
  if not new_version:
    flask.abort(400, "missing thing_version.")
  new_vesion = int(new_version)

  store.thing_write_update(thing_id, new_version, raw_body)
  return {'thing_version': new_vesion}

@app.get("/imgs/<img_id>")
def serve_imgs_get(img_id):
  return store.img_get(img_id)

@app.post("/imgs")
def serve_imgs_post():
  file = flask.request.files["file"]

  content_type = file.content_type
  ext = EXTENSIONS.get(content_type)
  if not ext:
    flask.abort(400, "unknown content type.")

  img_id = store.img_write_new(file, content_type, ext)
  return {
    "url": f"/imgs/{img_id}"
  }


if __name__ == "__main__":
  app.run(host="0.0.0.0")
