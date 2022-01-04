from flask import (
    Flask,
    jsonify,
    request,
    url_for,
    redirect,
    session,
    render_template,
    g,
    request,
)
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)


# close the connection once the route is visited
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, "sqlite_db"):
        g.sqlite_db.close()


# get user properties if he exist in the session
def get_current_user():
    user_properties = None
    if "name" in session:
        name = session["name"]
        db = get_db()
        user_cur = db.execute(
            """select id, name, expert, admin 
            from users 
            where name=(?)""",
            [name],
        )
        user_properties = user_cur.fetchone()

    return user_properties


@app.route("/", methods=["GET", "POST"])
def index():

    # get user_properties if exist in session
    user_properties = get_current_user()

    db = get_db()
    questions_cur = db.execute(
        """ select 
                questions.id as question_id,
                questions.question_text,
                askers.name as asker_name,
                experts.name as expert_name
            from questions 
            join users as askers on askers.id = questions.asked_by_id 
            join users as experts on experts.id = questions.expert_id 
            where questions.answer_text is not null """
    )
    questions_db = questions_cur.fetchall()

    # render home base on existance of user in the session
    return render_template("home.html", user=user_properties, questions=questions_db)


@app.route("/register", methods=["GET", "POST"])
def register():

    # get user_properties if exist from the session
    user_properties = get_current_user()

    # for post request: insert user_properties to database
    if request.method == "POST":
        db = get_db()

        # check if the name of the user already exist
        existing_user_cur = db.execute(
            """select id 
            from users 
            where name=?""",
            [request.form["name"]],
        )
        existing_user = existing_user_cur.fetchone()
        if existing_user:
            return render_template(
                "register.html",
                user=user_properties,
                error="User already exists !",
            )
        # hashing the password
        hashed_password = generate_password_hash(request.form["password"], "sha256")
        db.execute(
            "insert into users (name, hashed_password, expert, admin) values (?, ?, ?, ?)",
            [request.form["name"], hashed_password, "0", "0"],
        )
        db.commit()
        return redirect(url_for("login"))
    return render_template("register.html", user=user_properties)


@app.route("/login", methods=["GET", "POST"])
def login():

    # get user_properties if exist from the session
    user_properties = get_current_user()

    # for post request: check existance and get user_properties from database
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]

        db = get_db()
        user_cur = db.execute(
            """select name, hashed_password, expert, admin 
            from users where name=(?)""",
            [name],
        )
        db_credentials = user_cur.fetchone()

        # check user_properties exist
        if db_credentials is not None:
            # check user_name and user_password match with its database couterpart
            if db_credentials["name"] and check_password_hash(
                db_credentials["hashed_password"], password
            ):

                # successful login
                # create a session
                session["name"] = db_credentials["name"]
                return redirect(url_for("index"))

        # unsuccessful login
        return render_template(
            "login.html", user=user_properties, error="Unvalid name or password !"
        )
    return render_template("login.html", user=user_properties)


@app.route("/question/<question_id>")
def question(question_id):
    # get user_properties if exist from the session
    user_properties = get_current_user()

    db = get_db()
    question_cur = db.execute(
        """select 
            questions.question_text, 
            questions.answer_text, 
            askers.name as asker_name, 
            experts.name as expert_name
        from questions 
        join users as askers on askers.id = questions.asked_by_id 
        join users as experts on experts.id = questions.expert_id 
        where questions.id=? """,
        [question_id],
    )
    question_db = question_cur.fetchone()

    return render_template("question.html", user=user_properties, question=question_db)


@app.route("/answer/<question_id>", methods=["GET", "POST"])
def answer(question_id):

    # get user_properties if exist from the session
    user_properties = get_current_user()

    # redirect user to login if not logged in
    if not user_properties:
        return redirect(url_for("login"))

    # check if user is an admin if not redirect to index
    if user_properties["expert"] != 1:
        return redirect(url_for("index"))

    db = get_db()

    if request.method == "POST":
        answer = request.form["answer"]
        db.execute(
            """update questions 
            set answer_text=? where id=?""",
            [answer, question_id],
        )
        db.commit()
        return redirect(url_for("unanswered"))

    question_cur = db.execute(
        "select id, question_text from questions where id=?", [question_id]
    )
    question_db = question_cur.fetchone()

    return render_template("answer.html", user=user_properties, question=question_db)


@app.route("/ask", methods=["GET", "POST"])
def ask():

    # get user_properties if exist from the session
    user_properties = get_current_user()

    # redirect user to login if not logged in
    if not user_properties:
        return redirect(url_for("login"))

    db = get_db()

    # insert data of question to questions table in db
    if request.method == "POST":
        db.execute(
            "insert into questions (question_text, asked_by_id, expert_id) values (?, ?, ?)",
            [request.form["question"], user_properties["id"], request.form["expert"]],
        )
        db.commit()

        return redirect(url_for("index"))

    # getting all experts from database
    cur_experts = db.execute("select id, name from users where expert=1")
    experts_db = cur_experts.fetchall()

    return render_template("ask.html", user=user_properties, experts=experts_db)


@app.route("/unanswered")
def unanswered():

    # get user_properties if exist from the session
    user_properties = get_current_user()

    # redirect user to login if not logged in
    if not user_properties:
        return redirect(url_for("login"))

    # check if user is an admin if not redirect to index
    if user_properties["expert"] != 1:
        return redirect(url_for("index"))

    db = get_db()
    question_cur = db.execute(
        """select questions.id, questions.question_text, users.name
           from questions 
           join users on users.id = questions.asked_by_id 
           where questions.answer_text is null and questions.expert_id=?""",
        [user_properties["id"]],
    )
    questions_db = question_cur.fetchall()

    return render_template(
        "unanswered.html", user=user_properties, questions=questions_db
    )


@app.route("/users")
def users():

    # get user_properties if exist from the session
    user_properties = get_current_user()

    # redirect user to login if not logged in
    if not user_properties:
        return redirect(url_for("login"))

    # check if user is an admin if not redirect to index
    if user_properties["admin"] != 1:
        return redirect(url_for("index"))

    # get all users from database
    db = get_db()
    users_cur = db.execute("select id, name, expert, admin from users")
    users_db = users_cur.fetchall()

    # send users_db to template
    return render_template("users.html", user=user_properties, users=users_db)


# to promote regular user to expert
@app.route("/promote/<user_id>")
def promote(user_id):

    # get user_properties if exist from the session
    user_properties = get_current_user()

    # redirect user to login if not logged in
    if not user_properties:
        return redirect(url_for("login"))

    # check if user is an admin if not redirect to index
    if user_properties["admin"] != 1:
        return redirect(url_for("index"))

    db = get_db()
    cur_user = db.execute("select expert from users where id=(?)", [user_id])
    db_user = cur_user.fetchone()
    if db_user["expert"] == 0:
        db.execute("update users set expert=1 where id=(?)", [user_id])
        db.commit()
        return redirect(url_for("users"))

    if db_user["expert"] == 1:
        db.execute("update users set expert=0 where id=(?)", [user_id])
        db.commit()

    return redirect(url_for("users"))


@app.route("/logout")
def logout():
    session.pop("name", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
