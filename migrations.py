from app import app, db
from app import Location  # Import your models

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Commit the changes
        db.session.commit()
        
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 