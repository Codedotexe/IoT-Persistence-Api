from flask import Flask, request, render_template, make_response, abort, Response, redirect
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
import getpass
import json
import os

app = Flask(__name__)

# Load default config and override config from an environment variable
os.makedirs(app.instance_path, exist_ok=True)
app.config.update({
	"SQLALCHEMY_DATABASE_URI": "sqlite:///" + os.path.join(app.instance_path, "database.db"),
	"SQLALCHEMY_TRACK_MODIFICATIONS": False
})
if os.path.isfile(os.path.join(app.instance_path, "config.json")):
	app.config.from_file(os.path.join(app.instance_path, "config.json"))
app.config.from_envvar("IOTPERSISTENCEAPI_SETTINGS", silent=True)

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

def initDB(adminPassword):
	# Create database and admin user
	db.create_all()
	passwordHash = generate_password_hash(adminPassword)
	admin = User(name="admin", isAdmin=1, passwordHash=passwordHash)
	db.session.add(admin)
	db.session.commit()

@app.cli.command("init-db")
def initDBCommand():
	adminPassword = getpass.getpass(prompt="Please choose an admin password: ")
	initDB(adminPassword)
	print("Initialized the databse")

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
@app.route("/admin", methods=["GET", "POST"])
@auth.login_required(role=["admin"])
def administrationPage():
	action = request.args.get("action")
	users = User.query.all()

	if action == "adduser": # Add a user
		username = request.form.get("username")
		password = request.form.get("password")
		isAdmin = request.form.get("isAdmin") is not None

		if validCredentials(username, password): # Are given credentials given (e.g. password min length)
			if User.query.filter_by(name=username).first() is not None: # Check if user with that name already exists
				return render_template("adminPage.html", users=users, msgType="error", msg="A user with that name already exists") # Error creating user
			else: # Proceed to add user to database
				passwordHash = generate_password_hash(password)
				app.logger.info(f"Adding username={username} and admin={isAdmin}")
				db.session.add(User(name=username, passwordHash=passwordHash, isAdmin=isAdmin))
				db.session.commit()

				users = User.query.all()
				return render_template("adminPage.html", users=users, msgType="success", msg="Successfully added user") # Successfully added user
		else: # Credentials are not valid or were None, return error message
			return render_template("adminPage.html", users=users, msgType="error", msg="Username or password are not valid") 
	
	elif action == "deluser": # Delete a user
		username = request.args.get("username")
		if username is not None:
			userQuery = User.query.filter_by(name=username).first()
			if userQuery is not None:
				db.session.delete(userQuery)
				db.session.commit()

				users = User.query.all()
				return render_template("adminPage.html", users=users, msgType="success", msg="Successfully deleted user") # Successfully deleted user
		return render_template("adminPage.html", users=users, msgType="error", msg="Can not delete user because user does not exist") # Error deleting user
	
	else: # Unknown action or no action given
		return render_template("adminPage.html", users=users)

# Admin html page which shows details about given user
@app.route("/admin/user")
@auth.login_required(role=["admin"])
def administrationUserDetails():
	username = request.args.get("username")
	if username != None:
		userQuery = User.query.filter_by(name=username).first()
		if userQuery != None:
			stateQueries = State.query.filter_by(user=username).all()
			return render_template("adminPageUserDetails.html", username=username, states=stateQueries)
	abort(404, "User not found")

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
		abort(404, "Key not found")
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

