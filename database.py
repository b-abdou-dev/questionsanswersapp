from flask import g
import psycopg2

from psycopg2.extras import (
    DictCursor,
)  # to retrun list of dictionaries instead of tuples

### setup database
#
# connect to database
def connect_db():
    # connection to postgres database with DictCursor type
    conn = psycopg2.connect(
        "postgres://mpqwnhgsoxinut:d780ad17d84422fe6861b67fb93e98870b2edc3f0f62e03a57df02ae9f139253@ec2-54-76-249-45.eu-west-1.compute.amazonaws.com:5432/d6egu1gprf2v68",
        cursor_factory=DictCursor,
    )

    # commits changes when ever query is executed
    conn.autocommit = True
    cur = conn.cursor()

    # retur db conn and cursor in dictionary
    db = {"conn": conn, "cur": cur}
    return db


def get_db():
    db = connect_db()

    # check if the connection established to globle object, if not create the connection
    if not hasattr(g, "postgres_db_conn"):  # g is globle object that tracks app data
        g.postgres_db_conn = db["conn"]

    # check if the cursor established to globle object, if not create the cursor
    if not hasattr(g, "postgres_db_cur"):  #
        g.postgres_db_cur = db["cur"]

    # return the cursor
    return g.postgres_db_cur


# initialize the database
def init_db():
    db = connect_db()
    db["cur"].execute(open("schema.sql", "r").read())
    db["cur"].close()
    db["conn"].close()


def init_admin():
    db = connect_db()
    db["cur"].execute("update users set admin = True where name = %s", ("David",))
    db["cur"].close()
    db["conn"].close()
