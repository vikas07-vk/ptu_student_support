from app import app, db, User, Admin
from werkzeug.security import generate_password_hash
# from scheduler import start_scheduler

if __name__ == '__main__':
    # start_scheduler()
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        print("Database tables recreated successfully")
        
        # Create admin user if it doesn't exist
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                email='admin@example.com'
            )
            db.session.add(admin)
            
            # Create a test user
            test_user = User(
                username='testuser',
                email='test@example.com',
                password=generate_password_hash('test123'),
                full_name='Test User',
                course='B.Tech',
                semester='4th',
                enrollment_number='12345'
            )
            db.session.add(test_user)
            
            try:
                db.session.commit()
                print("Admin user and test user created successfully")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating users: {e}")
    
    app.run(debug=True) 