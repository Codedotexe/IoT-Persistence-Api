from flask import Flask, request, render_template, make_response, abort, Response, redirect
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
import json
import os

# Init app
baseDir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config["DEBUG"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(baseDir, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# Declare models
class User(db.Model):
	name = db.Column(db.String, primary_key=True)
	passwordHash = db.Column(db.String, nullable=False)
	isAdmin = db.Column(db.Boolean, nullable=False)

	def __repr__(self):
		return f"User {self.name}"

class State(db.Model):
	key = db.Column(db.String, primary_key=True)
	value = db.Column(db.String, primary_key=True)
	user = db.Column(db.String, db.ForeignKey("user.name"), nullable=False)

	def __repr__(self):
		return f"State {self.key}={self.value}"

# Check if the given username and password meet standards
def validCredentials(username, password):
	app.logger.debug("Checking if given credentials are valid")
	if username == None or password == None:
		return False
	if len(username) < 1 or len(password) < 8:
		return False
	if not username.isascii():
		return False
	return True

# Authorization of user
@auth.verify_password
def verifyPassword(username, password):
	app.logger.debug(f"Authorizing user {username}")
	userQuery = User.query.filter_by(name=username).first()

	if userQuery != None and check_password_hash(userQuery.passwordHash, password):
		app.logger.debug("Authorization of user was successfull")
		return userQuery
	else:
		app.logger.debug("Authorization of user failed")
		return None

# Get user role (admin or normal user)
@auth.get_user_roles
def getUserRoles(user):
	app.logger.debug("Accessing user roles")
	if user.isAdmin:
		return ["admin"]
	else:
		return ["user"]

# Admin overview html page
@app.route("/admin")
@auth.login_required(role=["admin"])
def administrationPage():
	#action = request.args.get("action")

	users = User.query.all()
	return render_template("adminPage.html", users=users)

# Admin html page which shows details about given user
@app.route("/admin/user")
@auth.login_required(role=["admin"])
def administrationUserDetails():
	username = request.args.get("name")
	return render_template("adminPageUserDetails.html")

# Admin endpoint to add a user
@app.route("/admin/adduser", methods=["POST"])
@auth.login_required(role=["admin"])
def administrationAddUser():
	username = request.form.get("username")
	password = request.form.get("password")
	isAdmin = request.form.get("isAdmin") is not None


	if validCredentials(username, password):
		if User.query.filter_by(name=username).first() is not None:
			return abort(400, "A user with that name already exists")

		passwordHash = generate_password_hash(password)
		app.logger.info(f"Adding username={username} and admin={isAdmin}")
		db.session.add(User(name=username, passwordHash=passwordHash, isAdmin=isAdmin))
		db.session.commit()
		return redirect("/admin")
	else:
		abort(400, "Username or password are not valid")

# Admin endpoint to delete a user
@app.route("/admin/deluser")
@auth.login_required(role=["admin"])
def administrationDeleteUser():
	username = request.args.get("username")
	if username is not None:
		userQuery = User.query.filter_by(name=username).first()
		if userQuery is not None:
			db.session.delete(userQuery)
			db.session.commit()
			return redirect("/admin")
	abort(400, "Can not delete user because user does not exist")

# Api endpoint to set a state
@app.route("/set")
@auth.login_required
def setState():
	key = request.args.get("key")
	value = request.args.get("value")
	if key == None or value == None:
		abort(400, "Parameters missing")
	
	stateQuery = State.query.filter_by(key=key, user=auth.current_user().name).first()
	if stateQuery is None:
		db.session.add(State(key=key, value=value, user=auth.current_user().name))
	else:
		stateQuery.value = value # Update value
	db.session.commit()
	return "Success"

# Api endpoint to get a state
@app.route("/get")
@auth.login_required
def getState():
	key = request.args.get("key")
	if key == None:
		abort(400, "Parameter missing")

	stateQuery = State.query.filter_by(key=key, user=auth.current_user().name).first()
	if stateQuery is None:
		abort(404, "Key not found")
	else:
		return stateQuery.value

# Api endpoint to remove a state
@app.route("/del")
@auth.login_required
def removeState():
	key = request.args.get("key")
	if key == None:
		abort(400, "Parameter missing")

	if State.query.filter_by(key=key, user=auth.current_user().name).first() is None:
		abort(400, "Key not found")
	else:
		db.remove(State.query.filter_by(key=key, user=auth.current_user().name).first())
		db.session.commit()
		return "Successfully removed state"

# Api endpoint to list all set states of user
@app.route("/list")
@auth.login_required
def listStates():
	stateQueries = State.query.filter_by(user=auth.current_user().name).all()
	responseDict = dict()
	for stateQuery in stateQueries:
		responseDict[stateQuery.key] = stateQuery.value
	return responseDict

@app.route("/")
def defaultRoute():
	abort(404, "Use the api endpoints")

# Start the server
if __name__ == "__main__":
	app.run()

