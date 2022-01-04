from flask import g
import sqlite3

### setup database
#
# connect to database
def connect_db():
    sql = sqlite3.connect("./questions.db")
    # to get dictionaries instead of tuples
    sql.row_factory = sqlite3.Row
    return sql


def get_db():
    # check if the connection established to globle object, if not create the connection
    if not hasattr(g, "sqlite3"):  # g is globle object that tracks app data
        g.sqlite_db = connect_db()

    # return the connection
    return g.sqlite_db
