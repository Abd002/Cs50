import os
import requests

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")

# export API_KEY=pk_a95fbcb50cba4abb8dbd10ca99c993c6
# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

SELECT = 0
USERNAME = "name"
USERNAME_parents_id = -1
ID = -1
USERNAME_parents = "namedf"

@app.route("/")
def index():
    """Show portfolio of stocks"""
    return render_template("homepage.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if not request.form.get("TODO"):
            return render_template("failure.html", error="You missed Select option")
        if request.form.get("TODO") == "child":
            return redirect("/register2")
        elif request.form.get("TODO") == "parents":
            return redirect("/register1")
    else:
        return render_template("register.html")

@app.route("/register1", methods=["GET", "POST"])
def register1():
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template("failure.html", error="You missed username")
        # Ensure password was submitted
        elif not request.form.get("password") or not request.form.get("confirmation") or request.form.get("confirmation") != request.form.get("password"):
           return render_template("failure.html", error="You missed password or it not matching")

        if len(request.form.get("password")) < 8:
            return render_template("failure.html", error="Your password should be at least 8")

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) == 1:
            return render_template("failure.html", error="This username alread exist")

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get(
            "username"), generate_password_hash(request.form.get("password")))
        flash("Registered!")
        return redirect("/login")
    else:
        return render_template("register1.html")

@app.route("/register2", methods=["GET", "POST"])
def register2():
    if request.method == "POST":
        #TODO all mistakes
        if not request.form.get("username"):
            return render_template("failure.html", error="You missed username")
        if not request.form.get("parents_name"):
            return render_template("failure.html", error="There is no parents_name whit this name")
        elif not request.form.get("password") or not request.form.get("confirmation") or request.form.get("confirmation") != request.form.get("password"):
            return render_template("failure.html", error="You missed password or it not matching")

        if len(request.form.get("password")) < 8:
            return render_template("failure.html", error="Your password should be at least 8")

        rows = db.execute("SELECT * FROM sons WHERE username = ?", request.form.get("username"))
        if len(rows) == 1:
            return render_template("failure.html", error="This username alread exist")

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("parents_name"))

        if len(rows) != 1:
            return render_template("failure.html", error="There is no parents_name whit this name")

        parents_name = rows[0]["username"]
        parents_id = rows[0]["id"]

        if request.form.get("parents_name") != parents_name:
            return render_template("failure.html", error="There is no parents_name whit this name")

        db.execute("INSERT INTO sons (user_id, hash, username, parents_name) VALUES (?, ?, ?, ?)",
                   parents_id, generate_password_hash(request.form.get("password")), request.form.get("username"), request.form.get("parents_name"))
        flash("Registered!")
        return redirect("/login")
    else:
        return render_template("register2.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #TODO all mistakes
        select = request.form.get("TODO")
        if not request.form.get("TODO"):
            return render_template("failure.html", error="You missed Select option")
        if select == "parents":
            rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
                return render_template("failure.html", error="The account name or password that you have entered is incorrect.")
            global SELECT
            global USERNAME_parents_id
            global USERNAME_parents
            global USERNAME
            SELECT = 1
            session["user_id"] = rows[0]["id"]
            USERNAME_parents_id = rows[0]["id"]
            USERNAME_parents = request.form.get("username")

        elif select == "child":
            rows = db.execute("SELECT * FROM sons WHERE username = ?", request.form.get("username"))
            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
                return render_template("failure.html", error="The account name or password that you have entered is incorrect.")
            SELECT = 0
            global ID
            global USERNAME
            USERNAME = request.form.get("username")
            session["user_id"] = rows[0]["id"]
            USERNAME_parents_id = rows[0]["user_id"]
            USERNAME_parents = rows[0]["parents_name"]
            ID = rows[0]["id"]
        # Remember which user has logged in
        flash("Logged in!")
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/chat_select", methods=["GET", "POST"])
def chat_select():
    if request.method == "POST":
        global USERNAME
        USERNAME = request.form.get("select")
        return redirect("/chat")
    else:
        if SELECT == 1:
            rows = db.execute("SELECT * FROM sons WHERE user_id = ?", session["user_id"])
            return render_template("chat.html", rows=rows)
        if SELECT == 0:
            return redirect("/chat")

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "POST":
        global USERNAME
        global SELECT
        global ID
        global USERNAME_parents_id
        global USERNAME_parents

        rows = db.execute("SELECT * FROM sons WHERE username = ?", USERNAME)

        if SELECT == 1:
            chat = USERNAME_parents + ':' + request.form.get("text")
            db.execute("INSERT INTO chat (son_id, user_id, chat) VALUES (?, ?, ?)",
                       ID, USERNAME_parents_id, chat)
        if SELECT == 0:
            chat = USERNAME + ':' + request.form.get("text")
            db.execute("INSERT INTO chat (son_id, user_id, chat) VALUES (?, ?, ?)",
                       ID, USERNAME_parents_id, chat)

        return redirect("/chat")
    else:
        rows = db.execute("SELECT * FROM sons WHERE username = ?", USERNAME)
        if SELECT == 1:
            ID = rows[0]["id"]
        rows = db.execute("SELECT * FROM chat WHERE son_id = ? AND user_id = ?", ID, USERNAME_parents_id)
        return render_template("chat1.html", rows=rows)

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/geolocation_select", methods=["GET", "POST"])
def geolocation_select():
    if request.method == "POST":
        global SELECT
        global ID
        global USERNAME
        if SELECT == 1:
            USERNAME = request.form.get("select")
            rows = db.execute("SELECT * FROM sons WHERE username = ?", USERNAME)
            ID = rows[0]["id"]
            return redirect("/geolocation")
    else:
        if SELECT == 1:
            rows = db.execute("SELECT * FROM sons WHERE user_id = ?", session["user_id"])
            return render_template("geolocation1.html", rows=rows)
        if SELECT == 0:
            return redirect("/geolocation")

@app.route("/geolocation", methods=["GET", "POST"])
def geolocation():
    if request.method == "POST":
        global SELECT
        global ID
        global USERNAME_parents_id
        if SELECT == 0:
            location = request.form.get("username")
            rows = db.execute("SELECT * FROM location WHERE son_id = ? AND user_id = ?", ID, USERNAME_parents_id)
            if len(rows) == 1:
                db.execute("UPDATE location SET lat=? WHERE user_id = ? AND son_id = ?", location, USERNAME_parents_id, ID)
                db.execute("UPDATE location SET lon=? WHERE user_id = ? AND son_id = ?", location, USERNAME_parents_id, ID)
                flash("Your geolocation has been updated!")
                return redirect("/")
            else:
                db.execute("INSERT INTO location (user_id, son_id, lat, lon) VALUES (?, ?, ?, ?)", USERNAME_parents_id, ID, location, location)
                return redirect("/")
        if SELECT == 1:
            return redirect("/")
    else:
        if SELECT == 1:
            rows = db.execute("SELECT * FROM location WHERE son_id = ? AND user_id = ?", ID, session["user_id"])
            if len(rows) == 1:
                location = "https://www.google.com/maps/search/" + rows[0]['lon']
                return render_template("geolocation2.html", rows=rows, location=location)
            else:
                return render_template("failure.html", error="Your son hasn't insert his location yet")
        if SELECT == 0:
            return render_template("geolocation.html")