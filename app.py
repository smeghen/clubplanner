import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
if os.path.exists("env.py"):
    import env


# -----------Configuration  -------------------
app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


# -------- Home Page -------------------------
@app.route("/")
@app.route("/get_events")
def get_events():
    # Sort all Created Events and display the next 3 events from todays date
    all_events = list(mongo.db.events.find())
    today_date = date.today()
    events = list()

    for event in all_events:
        event_date = datetime.strptime(event.get(
            'event_date'), '%d %B %Y').date()
        if event_date > today_date:
            event['event_date'] = event_date
            events.append(event)
    events.sort(key=lambda x: x['event_date'])

    events = events[:3]

    for event in events:
        event['event_date'] = datetime.strftime(
            event.get('event_date'), '%d %B %Y')
    return render_template("events.html", events=events)


@app.route("/summary")
def summary():
    all_events = list(mongo.db.events.find())
    today_date = date.today()
    events = list()

    for event in all_events:
        event_date = datetime.strptime(event.get(
            'event_date'), '%d %B %Y').date()
        if event_date > today_date:
            event['event_date'] = event_date
            events.append(event)
    events.sort(key=lambda x: x['event_date'])

    for event in events:
        event['event_date'] = datetime.strftime(
            event.get('event_date'), '%d %B %Y')
    return render_template("summary.html", events=events)


# Search function for taking user input and search db for relevant results
@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    events = list(mongo.db.events.find({"$text": {"$search": query}}))
    return render_template("events.html", events=events)


# Register a new user to the db ---------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if username already exists on DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        # Error message if Username already been used
        if existing_user:
            flash("This Username already Exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
            }
        mongo.db.users.insert_one(register)
        session["user"] = request.form.get("username").lower()
        flash("Congratulations you are now Registered")
        return redirect(url_for(
            "manage", username=session["user"]))

    return render_template("register.html")


# Login for Existing users -----------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if username already exists on DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # Check password matches DB
            if check_password_hash(
                 existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                return redirect(url_for("manage", username=session["user"]))

            else:
                # incorrect password
                flash("Incorrect Log In")
                return redirect(url_for("login"))

        else:
            # incorrect username
            flash("Incorrect Log In")
            return redirect(url_for("login"))
    return render_template("login.html")


# ------- Logout ----------------------------------
@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("Successfully logged out")
    session.pop("user")
    return redirect(url_for("get_events"))


# User Profile function for displaying Events created by them
@app.route("/manage/<username>", methods=["GET", "POST"])
def manage(username):
    # grab the session user's username from db and search db
    user = mongo.db.users.find_one({"username": username.lower()})
    events = mongo.db.events.find({"created_by": username.lower()})

    if "user" in session:
        return render_template(
            "manage.html", user=user, events=events)

    return redirect(url_for("login"))


# Create an Event ----------------------------------------
@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if "user" in session:
        if request.method == "POST":
            # check if Facility is already booked for Date and time
            date = request.form.get("event_date")
            time = request.form.get("event_time")
            venue = request.form.get("facility_name")
            if mongo.db.events.find_one(
                    {"event_date": date,
                     "event_time": time,
                     "facility_name": venue}
                    ):
                flash("Facility already booked!")
                return redirect(url_for("add_event"))
            # If facility free then details passed to db
            event = {
                "event_name": request.form.get("event_name"),
                "facility_name": request.form.get("facility_name"),
                "event_description": request.form.get("event_description"),
                "event_date": request.form.get("event_date"),
                "event_time": request.form.get("event_time"),
                "group_name": request.form.get("group_name"),
                "created_by": session["user"]
            }
            mongo.db.events.insert_one(event)
            flash("Event Successfully Added")
            return redirect(url_for("manage", username=session["user"]))
        facilities = mongo.db.facilities.find().sort("facility_name", 1)
        groups = mongo.db.groups.find()
        return render_template(
            "add_event.html", facilities=facilities, groups=groups)

    return redirect(url_for("login"))


# Edit events that the user has created ----------------------------------
@app.route("/edit_event/<event_id>", methods=["GET", "POST"])
def edit_event(event_id):
    if "user" in session:
        if request.method == "POST":
            # check if Facility is already booked for Date and time
            date = request.form.get("event_date")
            time = request.form.get("event_time")
            venue = request.form.get("facility_name")

            if mongo.db.events.find_one(
                    {"event_date": date,
                     "event_time": time,
                     "facility_name": venue,
                     "_id": {"$ne": ObjectId(event_id)}}
                    ):
                flash("Facility already booked!")
                return redirect(url_for('manage', username=session["user"]))

            # If facility free db updated
            submit = {
                "event_name": request.form.get("event_name"),
                "facility_name": request.form.get("facility_name"),
                "event_description": request.form.get("event_description"),
                "event_date": request.form.get("event_date"),
                "event_time": request.form.get("event_time"),
                "group_name": request.form.get("group_name"),
                "created_by": session["user"]
                }
            mongo.db.events.update({"_id": ObjectId(event_id)}, submit)
            flash("Event Updated")
            return redirect(url_for('manage', username=session["user"]))

        event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
        facilities = mongo.db.facilities.find().sort("facility_name", 1)
        groups = mongo.db.groups.find()
        return render_template(
            "edit_event.html", event=event,
            facilities=facilities, groups=groups)

    return redirect(url_for("login"))


# Delete an event that a user has created ----------------------------------
@app.route("/delete_event/<event_id>")
def delete_event(event_id):
    # Remove event from db
    if "user" in session:
        mongo.db.events.remove({"_id": ObjectId(event_id)})
        flash("Event Successfully Deleted")
        return redirect(url_for('manage', username=session["user"]))

    return redirect(url_for("login"))


# ------------ Error Handlers --------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    #  404 error function
    return render_template('404.html', error=error), 404


@app.errorhandler(500)
def internal_error(error):
    # 500 error function
    return render_template('500.html', error=error), 500


# ------------Run App ------------------------------------------------
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
