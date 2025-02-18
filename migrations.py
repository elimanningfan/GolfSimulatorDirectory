from app import app, db
from flask_migrate import upgrade

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    init_db() 