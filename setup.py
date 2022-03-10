from setuptools import setup

setup(
	name='IOT-Persistance-Api',
	version='0.0.1',
	packages=['iotpersistanceapi'],
	install_requires=[
		'flask',
		'flask-httpauth',
		'flask-sqlalchemy',
		'werkzeug',
		'importlib; python_version >= "3.6"',
	]
)
