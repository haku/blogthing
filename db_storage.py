from contextlib import contextmanager
from datetime import datetime
from datetime import timezone
from pathlib import Path
from psycopg_pool import ConnectionPool
import flask
import hashlib
import json
import os
import re

from filetypes import TYPE_TO_EXTENSION


THING_ID_PATTERN = re.compile(r'^[0-9a-f]{1,10}$')
IMG_ID_PATTERN = re.compile(r'^[0-9a-f]{64}.[a-z]{3,4}$')

class DbStorage:

  def __init__(self):
    self.db_pool = ConnectionPool(
        f"dbname=blogthing",
        check=ConnectionPool.check_connection,
        kwargs={"autocommit": True})
    self.mk_tables()

  def close(self):
    self.db_pool.close()


  def thing_list(self):
    with self.cursor() as cur:
      cur.execute("SELECT id, version, updated, title FROM things ORDER BY updated DESC")
      return [
          {
            "id": r[0],
            "version": r[1],
            "updated": int(r[2].timestamp()),
            "title": r[3],
          }
          for r in cur
      ]

  def thing_get(self, thing_id):
    self._thing_check_id(thing_id)
    with self.cursor() as cur:
      cur.execute("SELECT content, version FROM things WHERE id=%s", (thing_id,))
      row = cur.fetchone()
      if row is None:
        flask.abort(404, "thing not found.")

      if row[0] is None or len(row[0]) < 1:
        return {"thing_version": row[1]}

      return flask.Response(row[0], mimetype="application/json; charset=utf-8")

  def thing_new_id(self):
    with self.cursor() as cur:
      cur.execute("INSERT INTO things (created) VALUES (%s) RETURNING id",
                  (datetime.now(timezone.utc),))
      row = cur.fetchone()
      if row is None:
        flask.abort(404, "inserting new thing failed.")
      new_id = str(row[0])
      self._thing_check_id(new_id)
      return {"thing_id": new_id}

  def thing_write_update(self, thing_id, new_version, title, body):
    self._thing_check_id(thing_id)
    with self.cursor() as cur:
      cur.execute("SELECT version FROM things WHERE id=%s", (thing_id,))
      row = cur.fetchone()
      if row is None:
        flask.abort(404, "thing not found.")

      existing_version = row[0]
      if new_version <= existing_version:
        flask.abort(400, f"new version {new_version} <= existing version {existing_version}.")

      updated_time = datetime.now(timezone.utc)
      cur.execute(
          "UPDATE things SET version=%s, updated=%s, title=%s, content=%s WHERE id=%s",
          (new_version, updated_time, title, body, thing_id))

  def _thing_check_id(self, thing_id):
    if not THING_ID_PATTERN.match(thing_id):
      flask.abort(400, "invalid thing_id.")

  def img_list(self):
    with self.cursor() as cur:
      cur.execute("SELECT id, created, type, length(data) FROM imgs ORDER BY created DESC")
      return [
          {
            "id": r[0],
            "extension": TYPE_TO_EXTENSION[r[2]],
            "created": int(r[1].timestamp()),
            "type": r[2],
            "size": r[3],
          }
          for r in cur
      ]

  def img_get(self, img_id):
    self._img_check_id(img_id)
    img_id = img_id.rsplit(".", 1)[0]

    with self.cursor() as cur:
      cur.execute("SELECT type, data FROM imgs WHERE id=%s", (img_id,))
      row = cur.fetchone()
    if row is None:
      flask.abort(404, "img not found.")

    if flask.request.if_none_match.contains(img_id):
      return flask.Response(status=304)

    content_type, data = row
    resp = flask.Response(data, mimetype=content_type)
    resp.set_etag(img_id)
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp

  def img_write_new(self, file, content_type, extension):
    data = file.read()
    img_id = hashlib.sha256(data).hexdigest()
    file.seek(0)
    with self.cursor() as cur:
      cur.execute("INSERT INTO imgs (id, created, type, data) "
                  "VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                  (img_id, datetime.now(timezone.utc),
                   content_type, data))
    return f"{img_id}.{extension}"

  def _img_check_id(self, img_id):
    if not IMG_ID_PATTERN.match(img_id):
      flask.abort(400, "invalid img_id.")

  @contextmanager
  def cursor(self):
    with self.db_pool.connection() as conn:
      with conn.transaction():
        with conn.cursor() as cur:
          yield cur

  def mk_tables(self):
    with self.cursor() as cur:
      cur.execute(
          "CREATE TABLE IF NOT EXISTS things ("
          "id SERIAL PRIMARY KEY,"
          "version INTEGER NOT NULL DEFAULT 0,"
          "created TIMESTAMP WITH TIME ZONE NOT NULL,"
          "updated TIMESTAMP WITH TIME ZONE,"
          "title CHARACTER VARYING(500),"
          "content TEXT"
          ")")
      cur.execute(
          "CREATE TABLE IF NOT EXISTS imgs ("
          "id CHARACTER VARYING(64) PRIMARY KEY,"
          "created TIMESTAMP WITH TIME ZONE NOT NULL,"
          "type TEXT NOT NULL,"
          "data BYTEA NOT NULL,"
          "thumb BYTEA"
          ")")
