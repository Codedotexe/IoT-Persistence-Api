# IoT Persistence Api
## Description
This is a simple Python Flask server which implements a small api to allow users to store key-value pairs. It was created to store persistent states because IFTTT does not really allow you to do that.

## Installation
1. Download wheel file from releases tab
2. Create a new folder, enter it and execute `python -m venv .`
3. Activate virtual enviorment with `. bin/activate`
4. Install wheel file with pip: `pip install releasefile.whl`
5. Make sure a `var` folder exists in virtualenv, if not create it by runing `mkdir var`
6. Initialize database by running `export FLASK_APP='iotpersistenceapi'` and then `flask init-db` and set a admin password

## Configuration
The server looks for the existence of an `config.json` file in the flask instence folder and then loads it (the instance folder should be located in the var folder).

Example config.json:
```
{
	"SECREY_KEY": "YOURSECREYKEY"
}
```
You should set a `SECREY_KEY` in this config for security reasons, to do this just generate a random string with `python -c 'import secrets; print(secrets.token_hex())'` and set it in the config file.


## Run
Project can now be run with `flask run`. For production you should probably choose a cgi server like fastcgi ([further infos](https://flask.palletsprojects.com/en/2.0.x/tutorial/deploy/)).

## Usage
### Authentification
The api uses standard HTTP-Authentification using a username and a password. The user and it's password have to be created by the admin using the admin interface.

### Set a value
`/iotpersistenceapi/set?key=SOMEKEY&value=SOMEVALUE`
Returns 200 status code on success and 400 on failure.

### Get a value
`/iotpersistenceapi/get?key=SOMEKEY`
The value will be returned directly in plain text (not json).
Returns 200 status code on success, 404 on unknown key and 400 on other failures.

### Delete a value
`/iotpersistenceapi/del?key=SOMEKEY`
Returns 200 status code on success, 404 on unknown key and 400 on other failures.

### List values
`/iotpersistenceapi/list`
Returns key-value pairs in JSON format.

### Admin Interface
`/iotpersistenceapi/admin`

### Create new users
Can be done using the admin interface

### Note: IFTTT Webhooks HTTP-Auth
HTTP Authentification in IFTTT Webhooks can be achieved with the following synthax: `https://username:password@website.com`
