from app import db, User
from werkzeug.security import generate_password_hash
import getpass

# Create database
db.create_all()

# Create admin user
password = getpass.getpass(prompt="Please choose an admin password: ")
passwordHash = generate_password_hash(password)
admin = User(name="admin", isAdmin=1, passwordHash=passwordHash)
db.session.add(admin)

# Save changes
db.session.commit()

print("All operations completed successfully")

