#!/usr/bin/env python
# https://flask.palletsprojects.com/en/stable/quickstart/
# run: $ gunicorn server:app

import flask
import json

from filetypes import TYPE_TO_EXTENSION
import db_storage


store = db_storage.DbStorage()

app = flask.Flask(
    __name__,
    static_url_path='',
    static_folder='static')

@app.route("/")
def serve_root():
  return flask.send_file("static/index.html")

@app.get("/things")
def serve_things_root_get():
  return store.thing_list()

@app.post("/things")
def serve_things_root_post():
  if not flask.request.headers.get("Content-Type") == "application/json":
    flask.abort(400, "invalid content_type.")

  raw_body = flask.request.get_data(as_text=True)
  body = json.loads(raw_body)
  if not "action" in body:
    flask.abort(400, "missing action.")

  match body["action"]:
    case "new":
      return store.thing_new_id()
    case _:
      flask.abort(400, "unknown action.")

@app.get("/things/<thing_id>")
def serve_things_get(thing_id):
  return store.thing_get(thing_id)

@app.post("/things/<thing_id>")
def serve_things_post(thing_id):
  if not flask.request.headers.get("Content-Type") == "application/json":
    flask.abort(400, "invalid content_type.")
  # TODO enforce max length etc
  # TODO validate thing_date

  raw_body = flask.request.get_data(as_text=True)
  body = json.loads(raw_body)

  new_version = body.get('thing_version')
  if not new_version:
    flask.abort(400, "missing thing_version.")
  new_vesion = int(new_version)

  published = body.get('thing_published')
  if not isinstance(published, bool):
    flask.abort(400, "missing or invalid thing_published.")

  title = body.get('thing_title')

  store.thing_write_update(thing_id, new_version, published, title, raw_body)
  return {'thing_version': new_vesion}

@app.get("/versions/<thing_id>")
def serve_versions_list(thing_id):
  return store.versions_list(thing_id)

@app.get("/versions/<thing_id>/<version>")
def serve_versions_get(thing_id, version):
  return store.version_get(thing_id, version)

@app.get("/imgs")
def serve_imgs_root_get():
  return store.img_list()

@app.get("/imgs/<img_id>")
def serve_imgs_get(img_id):
  return store.img_get(img_id)

@app.post("/imgs")
def serve_imgs_post():
  # TODO enforce max length etc
  file = flask.request.files["file"]

  content_type = file.content_type
  ext = TYPE_TO_EXTENSION.get(content_type)
  if not ext:
    flask.abort(400, "unknown content type.")

  img_id = store.img_write_new(file, content_type, ext)
  return {
    "url": f"/imgs/{img_id}"
  }


if __name__ == "__main__":
  app.run(host="127.0.0.1", port=9456)
  store.close()
