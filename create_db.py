from app import app, db

with app.app_context():
    db.drop_all()  # Drop existing tables
    db.create_all()  # Create tables with new schema
    print("Database tables created successfully!") 