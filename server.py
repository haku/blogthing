#!/usr/bin/env python
# https://flask.palletsprojects.com/en/stable/quickstart/
# run: $ gunicorn server:app

from authlib.integrations.flask_client import OAuth
import cachelib
import flask
import flask_compress
import flask_session
import json
import os

from filetypes import TYPE_TO_EXTENSION
import db_storage


store = db_storage.DbStorage()

app = flask.Flask(
    __name__,
    static_url_path='',
    static_folder='static')

app.config['SESSION_TYPE'] = 'cachelib'
app.config['SESSION_CACHELIB'] = cachelib.SimpleCache(threshold=500)
flask_session.Session(app)

oauth = OAuth(app)
oauth.register(
    'openid',
    client_id=os.environ['OPENID_CLIENT_ID'],
    client_secret=os.environ['OPENID_CLIENT_SECRET'],
    server_metadata_url=os.environ['OPENID_METADATA_URL'],
    client_kwargs={'scope': 'openid profile email'})

@app.route('/authorize')
def authorize():
  token = oauth.openid.authorize_access_token()
  info = token.get('userinfo')
  if info:
    flask.session['auth_name'] = info['name']
    print(f"Auth successful, session: {flask.session}")
    return flask.redirect('/')
  else:
    flask.abort(400, "Auth token missing userinfo.")

@app.before_request
def require_login():
  if flask.request.endpoint in ['authorize', 'static']:  # method name
    return None
  if flask.session.get('auth_name'):
    return None
  redirect_uri = flask.url_for('authorize', _external=True)
  return oauth.openid.authorize_redirect(redirect_uri)


@app.route("/")
def serve_root():
  return flask.send_file("static/index.html")

@app.get("/api/things")
def serve_things_root_get():
  include = flask.request.args.getlist("t")
  exclude = flask.request.args.getlist("e")
  return store.thing_list(include, exclude)

@app.post("/api/things")
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

@app.get("/api/things/<thing_id>")
def serve_things_get(thing_id):
  return store.thing_get(thing_id)

@app.get("/api/things/<thing_id>/version")
def serve_things_get_version(thing_id):
  return store.thing_get_version(thing_id)

@app.post("/api/things/<thing_id>")
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

  tags = body.get('thing_tags')
  if not isinstance(published, bool):
    flask.abort(400, "missing or invalid thing_tags.")

  store.thing_write_update(thing_id, new_version, published, title, raw_body)
  store.tags_replace(thing_id, tags)

  return {'thing_version': new_vesion}

@app.get("/api/versions/<thing_id>")
def serve_versions_list(thing_id):
  return store.versions_list(thing_id)

@app.get("/api/versions/<thing_id>/<version>")
def serve_versions_get(thing_id, version):
  return store.version_get(thing_id, version)

@app.get("/api/tags/top")
def serve_tags_top():
  return store.tags_top()

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
  flask_compress.Compress().init_app(app)
  app.run(host="127.0.0.1", port=9456)
  store.close()
