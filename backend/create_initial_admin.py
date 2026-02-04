from backend import models, database, utils

def create_initial_admin(name="admin", password="admin"):
    db = database.SessionLocal()
    # Ensure tables exist
    models.Base.metadata.create_all(bind=database.engine)
    try:
        if db.query(models.Team).filter(models.Team.name == name).first():
            print(f"Admin '{name}' already exists.")
            return

        hashed_password = utils.get_password_hash(password)
        admin_user = models.Team(
            name=name, 
            password_hash=hashed_password, 
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin '{name}' created successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_admin()
