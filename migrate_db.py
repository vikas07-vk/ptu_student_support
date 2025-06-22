from app import db, app
import sqlite3

def migrate_database():
    with app.app_context():
        # Connect to the database
        conn = sqlite3.connect('student_portal.db')
        cursor = conn.cursor()
        
        try:
            # Check if profile_photo column exists
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'profile_photo' not in columns:
                # Add profile_photo column
                cursor.execute("ALTER TABLE user ADD COLUMN profile_photo VARCHAR(200)")
                print("Successfully added profile_photo column to user table")
            else:
                print("profile_photo column already exists")
            
            # Drop notice table if it exists
            cursor.execute("DROP TABLE IF EXISTS notice")
            print("Dropped existing notice table")
            
            # Create notice table with correct schema
            cursor.execute("""
                CREATE TABLE notice (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(500) NOT NULL,
                    date_posted DATETIME NOT NULL,
                    link VARCHAR(500) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Created notice table with correct schema")
            
            # Commit the changes
            conn.commit()
            print("Migration completed successfully")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == '__main__':
    migrate_database() 