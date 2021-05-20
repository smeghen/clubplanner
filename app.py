import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_events")
def get_events():
    events = mongo.db.events.find()
    return render_template("events.html", events=events)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if username already exists on DB
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("This Username already Exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "group_name": request.form.get("group_name")
            }
        mongo.db.users.insert_one(register)
        session["user"] = request.form.get("username").lower()
        flash("Congratulations you are now Registered")
        return redirect(url_for(
            "profile", username=session["user"]))
    groups = mongo.db.groups.find()
    return render_template("register.html", groups=groups)


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
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for("profile", username=session["user"]))
            
            else:
                #incorrect password
                flash("Incorrect Log In")
                return redirect(url_for("login"))

        else:
            # incorrect username
            flash("Incorrect Log In")
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    user = mongo.db.users.find_one({"username": username.lower()})
    users = mongo.db.users.find({"username": username.lower()})
    groups = mongo.db.groups.find()
    

    if "user" in session:    
        return render_template(
            "profile.html", user=user, users=users, groups=groups)

    return redirect(url_for(login))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("Successfully logged out")
    session.pop("user")
    return redirect(url_for("get_events"))


@app.route("/manage/<username>", methods=["GET", "POST"])
def manage(username):
    # grab the session user's username from db
    user = mongo.db.users.find_one({"username": username.lower()})
    events = mongo.db.events.find({"created_by": username.lower()})

    if "user" in session:    
        return render_template(
            "manage.html", user=user, events=events)

    return redirect(url_for(login))


@app.route("/add_event", methods=["GET", "POST"])
def add_event():
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
        flash("Task Successfully Added")
        return redirect(url_for("get_events"))
    facilities = mongo.db.facilities.find().sort("facility_name", 1)
    groups = mongo.db.groups.find()
    return render_template(
        "add_event.html", facilities=facilities, groups=groups)


@app.route("/edit_event/<event_id>", methods=["GET", "POST"])
def edit_event(event_id):
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
            return redirect(url_for('profile', username=session["user"]))

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
        flash("Task Successfully Updated")
            
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    facilities = mongo.db.facilities.find().sort("facility_name", 1)
    groups = mongo.db.groups.find()
    return render_template(
        "edit_event.html", event=event, facilities=facilities, groups=groups)


@app.route("/delete_event/<event_id>")
def delete_event(event_id):
    mongo.db.events.remove({"_id": ObjectId(event_id)})
    flash("Event Successfully Deleted")
    return redirect(url_for('profile', username=session["user"]))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)