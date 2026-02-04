from backend import models, database, utils

db = database.SessionLocal()
user = db.query(models.Team).filter(models.Team.name == "admin").first()

if not user:
    print("User 'admin' NOT FOUND in DB!")
else:
    print(f"User 'admin' found. Is Admin: {user.is_admin}")
    print(f"Hash: {user.password_hash}")
    
    # Verify password
    if utils.verify_password("admin", user.password_hash):
        print("Password 'admin' VERIFIED successfully.")
    else:
        print("Password 'admin' FAILED verification.")

db.close()
