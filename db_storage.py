from contextlib import contextmanager
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from psycopg_pool import ConnectionPool
import flask
import hashlib
import json
import os
import re
import time

from filetypes import TYPE_TO_EXTENSION


THING_ID_PATTERN = re.compile(r'^[0-9a-f]{1,10}$')
VERSION_PATTERN = re.compile(r'^[0-9a-f]{1,10}$')
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


  def thing_list(self, tags):
    query = "SELECT id, version, updated, title, published FROM things ORDER BY updated DESC"
    args = ()
    if tags:
      query = ("SELECT DISTINCT id, version, updated, things.title, published "
               "FROM things "
               "LEFT JOIN tags ON tags.thing_id = things.id "
               "WHERE tags.title=ANY(%s) "
               "ORDER BY updated DESC")
      args = (tags,)

    with self.cursor() as cur:
      cur.execute(query, args)
      return [
          {
            "id": r[0],
            "version": r[1],
            "updated": int(r[2].timestamp()) if r[2] else None,
            "title": r[3],
            "published": r[4],
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
                  (self._now(),))
      row = cur.fetchone()
      if row is None:
        flask.abort(404, "inserting new thing failed.")
      new_id = str(row[0])
      self._thing_check_id(new_id)
      return {"thing_id": new_id}

  def thing_write_update(self, thing_id, new_version, published, title, body):
    self._thing_check_id(thing_id)
    with self.cursor() as cur:
      cur.execute("SELECT version FROM things WHERE id=%s", (thing_id,))
      row = cur.fetchone()
      if row is None:
        flask.abort(404, "thing not found.")

      existing_version = row[0]
      if new_version <= existing_version:
        flask.abort(400, f"new version {new_version} <= existing version {existing_version}.")

      now = self._now()
      cur.execute(
          "UPDATE things SET version=%s, updated=%s, published=%s, title=%s, content=%s WHERE id=%s",
          (new_version, now, published, title, body, thing_id))

    self._versions_add(thing_id, new_version, now, body)


  def versions_list(self, thing_id):
    with self.cursor() as cur:
      cur.execute("SELECT version, created, length(content) FROM versions "
                  "WHERE thing_id=%s "
                  "ORDER BY created DESC", (thing_id,))
      return [
          {
            "version": r[0],
            "updated": int(r[1].timestamp()),
            "length": r[2],
          }
          for r in cur
      ]

  def version_get(self, thing_id, version):
    self._thing_check_id(thing_id)
    self._version_check(version)
    with self.cursor() as cur:
      cur.execute("SELECT content FROM versions WHERE thing_id=%s AND version=%s",
                  (thing_id, version))
      row = cur.fetchone()
      if row is None:
        flask.abort(404, "thing version not found.")
      return flask.Response(row[0], mimetype="application/json; charset=utf-8")

  def _versions_add(self, thing_id, version, created, body):
    start = time.monotonic()
    with self.cursor() as cur:
      cur.execute("SELECT max(created) FROM versions WHERE thing_id=%s", (thing_id,))
      row = cur.fetchone()
      prev_created = row[0] if row is not None else None
      if prev_created is not None and self._now() - prev_created < timedelta(minutes=1):
        return
      cur.execute("INSERT INTO versions (thing_id, version, created, content) "
                  "VALUES (%s, %s, %s, %s)", (thing_id, version, created, body))
    vers = self._versions_prune(thing_id)
    print(f"Updated versions for thing={thing_id} in {round(time.monotonic() - start, 3)}s, "
          f"pruned: {vers}.")

  def _versions_prune(self, thing_id):
    with self.cursor() as cur:
      cur.execute(
          "WITH newest AS ("
          "  SELECT version"
          "  FROM versions"
          "  WHERE thing_id=%(id)s"
          "  ORDER BY version DESC"
          "  LIMIT 10"
          "),"
          "minutly AS ("
          "  SELECT version"
          "  FROM ("
          "    SELECT version, row_number() OVER ("
          "      PARTITION BY date_bin('5 minutes', created, TIMESTAMP '2025-01-01 00:00:00')"
          "      ORDER BY version ASC"
          "    ) AS rn"
          "    FROM versions"
          "    WHERE thing_id=%(id)s"
          "    AND created > NOW() - INTERVAL '3 hours'"
          "    AND version < (SELECT min(version) FROM newest)"
          "  )"
          "  WHERE rn = 1"
          "  LIMIT 36"
          "),"
          "hourly AS ("
          "  SELECT version"
          "  FROM ("
          "    SELECT version, row_number() OVER ("
          "      PARTITION BY date_trunc('hour', created)"
          "      ORDER BY version ASC"
          "    ) AS rn"
          "    FROM versions"
          "    WHERE thing_id=%(id)s"
          "    AND version < LEAST("
          "      (SELECT min(version) FROM newest),"
          "      (SELECT min(version) FROM minutly)"
          "    )"
          "  )"
          "  WHERE rn = 1"
          ")"
          "DELETE FROM versions"
          "  WHERE thing_id=%(id)s"
          "  AND version NOT IN ("
          "    SELECT version FROM newest"
          "    UNION"
          "    SELECT version FROM minutly"
          "    UNION"
          "    SELECT version FROM hourly"
          "  )"
          "RETURNING version",
          {"id": thing_id})
      return [r[0] for r in cur]

  def _thing_check_id(self, thing_id):
    if not THING_ID_PATTERN.match(thing_id):
      flask.abort(400, "invalid thing_id.")

  def _version_check(self, version):
    if not VERSION_PATTERN.match(version):
      flask.abort(400, "invalid version.")


  def tags_replace(self, thing_id, new_tags):
    new_tags = set(new_tags)
    with self.cursor() as cur:
      cur.execute("SELECT title FROM tags WHERE thing_id=%s", (thing_id,))
      existing = set([r[0] for r in cur])
      to_add = new_tags - existing
      to_rm = existing - new_tags
      print(f"to_add={to_add} to_rm={to_rm}")
      cur.executemany("INSERT INTO tags (thing_id, title) VALUES (%s, %s)",
                      [(thing_id, t) for t in to_add])
      cur.executemany("DELETE FROM tags WHERE thing_id=%s AND title=%s",
                      [(thing_id, t) for t in to_rm])

  def tags_top(self):
    with self.cursor() as cur:
      cur.execute("SELECT title, count(1) AS n FROM tags GROUP BY title ORDER BY n, title")
      return [
          {
            "title": r[0],
            "count": r[1],
          }
          for r in cur
      ]


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
                  (img_id, self._now(), content_type, data))
    return f"{img_id}.{extension}"

  def _img_check_id(self, img_id):
    if not IMG_ID_PATTERN.match(img_id):
      flask.abort(400, "invalid img_id.")

  def _now(self):
    return datetime.now(timezone.utc)

  @contextmanager
  def cursor(self):
    with self.db_pool.connection() as conn:
      with conn.transaction():
        with conn.cursor() as cur:
          yield cur

  def mk_tables(self):
    # TODO at some point going to want some indexes
    with self.cursor() as cur:
      cur.execute(
          "CREATE TABLE IF NOT EXISTS things ("
          "id SERIAL PRIMARY KEY,"
          "version INTEGER NOT NULL DEFAULT 0,"
          "created TIMESTAMP WITH TIME ZONE NOT NULL,"
          "updated TIMESTAMP WITH TIME ZONE,"
          "published BOOLEAN NOT NULL DEFAULT false,"
          "title CHARACTER VARYING(500),"
          "content TEXT"
          ")")
      # ALTER TABLE things ADD COLUMN published BOOLEAN NOT NULL DEFAULT false;
      cur.execute(
          "CREATE TABLE IF NOT EXISTS tags ("
          "thing_id INTEGER NOT NULL REFERENCES things(id),"
          "title CHARACTER VARYING(50),"
          "UNIQUE (thing_id, title)"
          ")")
      cur.execute(
          "CREATE TABLE IF NOT EXISTS versions ("
          "thing_id INTEGER NOT NULL,"
          "version INTEGER NOT NULL,"
          "created TIMESTAMP WITH TIME ZONE NOT NULL,"
          "content TEXT,"
          "UNIQUE (thing_id, version)"
          ")")
      cur.execute(
          "CREATE TABLE IF NOT EXISTS imgs ("
          "id CHARACTER VARYING(64) PRIMARY KEY,"
          "created TIMESTAMP WITH TIME ZONE NOT NULL,"
          "type TEXT NOT NULL,"
          "data BYTEA NOT NULL,"
          "thumb BYTEA"
          ")")
