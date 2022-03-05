#!/bin/sh
DB_PATH="$(dirname "$0")/database.db"

# Python script to hash password
read -r -d '' PYTHON_SCRIPT <<- EOM
	from werkzeug.security import generate_password_hash
	print(generate_password_hash("${PASSWORD}"))
EOM

# Sqlite script to create database
read -r -d '' SQLITE_SCRIPT <<- EOM
	PRAGMA foreign_keys = ON;

	CREATE TABLE user (
		name TEXT PRIMARY KEY,
		passwordHash TEXT NOT NULL,
		isAdmin INTEGER NOT NULL
	);

	CREATE TABLE state (
		key TEXT NOT NULL,
		value TEXT NOT NULL,
		user TEXT REFERENCES user NOT NULL,
		PRIMARY KEY (key, user)
	);
EOM


# Check if database already exists
if [ -f "$DB_PATH" ]; then
	echo 'Database already exists' >&2
	exit 1
fi

# Read password fom stdin
echo 'Please enter a password for the admin account'
read -s PASSWORD
echo 'Please confirm the password'
read -s PASSWORD2

# Check if the two passwords match
if [ "$PASSWORD" != "$PASSWORD2" ]; then
	echo 'Passwords do not match' >&2
	exit 1
fi

# Generate password hash using python
if PASSWORD_HASH="$(python -c "$PYTHON_SCRIPT")"; then
	echo 'Successfully hashed the password'
else
	echo 'Could not generate password hash' >&2
	exit 1
fi

# Create the database
echo 'Creating database'
if sqlite3 "$DB_PATH" "$SQLITE_SCRIPT"; then
	echo 'Successfully created database'
else
	echo 'Error during database creation' >&2
	exit 1
fi

# Create admin account
# INFO: Not sql injection safe
if sqlite3 "$DB_PATH" "INSERT INTO user (name,passwordHash,isAdmin) VALUES ('admin','$PASSWORD_HASH',1)"; then
	echo 'Successfully added admin account to database'
else
	echo 'Error while adding admin account to database' >&2
	exit 1
fi

