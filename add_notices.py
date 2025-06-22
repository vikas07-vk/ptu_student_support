import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3
import os

def fetch_ptu_notices():
    # URL of the PTU noticeboard
    url = "https://ptu.ac.in/noticeboard-main/"
    
    try:
        # Send GET request to the URL
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table containing notices
        notices = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:6]  # Get first 5 rows excluding header
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:  # Ensure we have at least title and date
                    title = cols[0].text.strip()
                    date_str = cols[1].text.strip()
                    link = cols[2].find('a')['href'] if cols[2].find('a') else "#"
                    
                    # Convert date string to datetime object
                    try:
                        date_posted = datetime.strptime(date_str, '%d/%m/%Y')
                    except ValueError:
                        date_posted = datetime.now()
                    
                    notices.append({
                        'title': title,
                        'date_posted': date_posted,
                        'link': link
                    })
        
        return notices
    
    except Exception as e:
        print(f"Error fetching notices: {e}")
        return []

def add_notices_to_db():
    # Get the absolute path of the database file
    db_path = os.path.join(os.path.dirname(__file__), 'student_portal.db')
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Fetch notices from PTU website
        notices = fetch_ptu_notices()
        
        # Clear existing notices
        cursor.execute("DELETE FROM notice")
        
        # Add new notices
        for notice in notices:
            cursor.execute("""
                INSERT INTO notice (title, date_posted, link, created_at, is_new)
                VALUES (?, ?, ?, datetime('now'), 1)
            """, (notice['title'], notice['date_posted'], notice['link']))
        
        # Commit the changes
        conn.commit()
        print(f"Successfully added {len(notices)} notices to the database")
        
    except Exception as e:
        print(f"Error adding notices to database: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    add_notices_to_db() 