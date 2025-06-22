from flask import Flask, render_template, request, jsonify, send_file, session
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
import os
import re
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import logging
from werkzeug.utils import secure_filename
import ptu_utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'your_secret_key_here'

# Configure upload folder
UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'miss.vanshika.sharma.10@gmail.com'
EMAIL_PASS = 'odsjfedptznuinhx'
ADMIN_EMAILS = ['miss.vanshika.sharma.10@gmail.com', 'vkviki0786@gmail.com']

# Initialize chatbot data
df = None
responses = {}
vectorizer = None
question_vectors = None

# Load chatbot data
try:
    # Load CSV file
    csv_path = 'Structured_Chatbot_Data    chatbot csv.csv'
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, encoding='utf-8')
        # Clean the data
        df['User Query (Pattern)'] = df['User Query (Pattern)'].fillna('')
        df['Bot Response'] = df['Bot Response'].fillna('')
        df['User Query (Pattern)'] = df['User Query (Pattern)'].astype(str)
        df['Bot Response'] = df['Bot Response'].astype(str)
        
        # Initialize TF-IDF vectorizer
        vectorizer = TfidfVectorizer()
        question_vectors = vectorizer.fit_transform(df['User Query (Pattern)'])
        
        print(f"Successfully loaded CSV file with {len(df)} rows")
    else:
        print(f"Warning: CSV file not found at {csv_path}")
    
    # Load responses JSON if exists
    json_path = 'data/responses.json'
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            responses = json.load(f)
            print("Successfully loaded responses JSON")
    else:
        print(f"Warning: JSON file not found at {json_path}")
        
except Exception as e:
    print(f"Error loading data: {str(e)}")

def clean_text(text):
    # Convert to lowercase and remove extra spaces
    text = str(text).lower().strip()
    # Remove punctuation except question marks
    text = re.sub(r'[^\w\s?]', '', text)
    return text

def find_best_match(user_message):
    if vectorizer is None or question_vectors is None:
        return None, -1
        
    # Clean and vectorize user message
    user_message = clean_text(user_message)
    user_vector = vectorizer.transform([user_message])
    
    # Calculate cosine similarity
    similarities = cosine_similarity(user_vector, question_vectors).flatten()
    best_match_idx = similarities.argmax()
    
    # Return best match if similarity is above threshold
    if similarities[best_match_idx] > 0.3:
        return df.iloc[best_match_idx]['Bot Response'], similarities[best_match_idx]
        
    return None, -1

def get_bot_response(user_message):
    try:
        if not user_message:
            return "Please enter a message."
            
        message_lower = user_message.lower().strip()
        
        # First check JSON responses
        if responses:
            # Check for hostel related keywords
            hostel_keywords = ["hostel", "hostels", "hostel application", "hostel facility", "hostel accommodation", 
                            "hostel room", "hostel fees", "hostel rules", "hostel registration", "hostel form"]
            
            if any(keyword in message_lower for keyword in hostel_keywords):
                return """IKGPTU provides hostel facilities for students. Here's how to apply for hostel:

1. Hostel Application Process:
   - Visit the university website and download the hostel application form
   - Fill out the form with your details
   - Submit the form along with required documents to the hostel office
   - Pay the hostel fees as per the fee structure

2. Required Documents:
   - Admission letter
   - ID proof
   - Passport size photographs
   - Medical fitness certificate
   - Parent/Guardian consent form

3. Hostel Facilities:
   - Separate hostels for boys and girls
   - 24/7 security
   - Mess facility
   - Common room
   - Wi-Fi connectivity
   - Laundry service
   - Medical facilities

For more details, please contact the hostel office at:
Email: hostel@ikgptu.edu.in
Phone: [University Contact Number]

Note: Hostel accommodation is subject to availability and university rules."""
        
            # Check other patterns in JSON
            for pattern, response in responses.items():
                if pattern.lower() in message_lower:
                    return response
        
        # Then check document requests
        if any(word in message_lower for word in ["fee", "fees"]):
            for course in ["btech", "mtech", "mba"]:
                if course in message_lower:
                    return f"You can find the {course.upper()} fee structure here: /download/fee_structure/{course}"
        
        if any(word in message_lower for word in ["timetable", "time table"]):
            for course in ["btech", "mtech", "mba"]:
                if course in message_lower:
                    return f"You can find the {course.upper()} timetable here: /download/timetable/{course}"
        
        if "syllabus" in message_lower:
            for course in ["btech", "mtech", "mba"]:
                if course in message_lower:
                    return f"You can find the {course.upper()} syllabus here: /download/syllabus/{course}"
        
        # Only if no JSON match found, try CSV data
        best_response, similarity = find_best_match(message_lower)
        if best_response is not None and similarity > 0.3:
            return best_response
        
        return "I apologize, but I don't have specific information about that. Please try rephrasing your question or ask something else."
        
    except Exception as e:
        logger.error(f"Error getting response: {str(e)}")
        return "I'm having trouble processing your request. Please try again."

@app.route('/')
def home():
    if 'chat_history' not in session:
        session['chat_history'] = []
        
    # Get current hour
    current_hour = datetime.now().hour
    
    # Determine greeting based on time of day
    if 5 <= current_hour < 12:
        greeting = "Good Morning! I am IKGPTU Assistant. How can I help you today?"
    elif 12 <= current_hour < 17:
        greeting = "Good Afternoon! I am IKGPTU Assistant. How can I help you today?"
    elif 17 <= current_hour < 21:
        greeting = "Good Evening! I am IKGPTU Assistant. How can I help you today?"
    else:
        greeting = "Hello! I am IKGPTU Assistant. How can I help you today?"
    
    # Add greeting to chat history
    session['chat_history'].append({
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'user_message': '',
        'bot_response': greeting
    })
    
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        # Get bot response
        bot_response = get_bot_response(user_message)
        
        # Update chat history
        chat_history = session.get('chat_history', [])
        current_time = datetime.now()
        
        # Remove messages older than 7 days
        chat_history = [msg for msg in chat_history 
                       if (current_time - datetime.strptime(msg['timestamp'], "%Y-%m-%d %H:%M:%S")) <= timedelta(days=7)]
        
        # Add new message
        chat_history.append({
            'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'user_message': user_message,
            'bot_response': bot_response
        })
        
        session['chat_history'] = chat_history
        
        return jsonify({'response': bot_response})
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your message'}), 500

@app.route('/live_support', methods=['POST'])
def live_support():
    try:
        # Try to get JSON data first
        json_data = request.get_json(silent=True)
        if json_data:
            name = json_data.get('name')
            email = json_data.get('email')
            query = json_data.get('query')
        else:
            # If no JSON, try form data
            name = request.form.get('name')
            email = request.form.get('email')
            query = request.form.get('query')

        # Log received data
        logger.info(f"Received support request - Name: {name}, Email: {email}")

        # Validate data
        if not all([name, email, query]):
            missing = []
            if not name: missing.append("name")
            if not email: missing.append("email")
            if not query: missing.append("query")
            logger.error(f"Missing fields in support request: {', '.join(missing)}")
            return jsonify({
                'success': False,
                'message': f'कृपया सभी आवश्यक फ़ील्ड भरें: {", ".join(missing)}'
            })

        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = ", ".join(ADMIN_EMAILS)
            msg['Subject'] = f"Live Support Request from {name}"
            
            body = f"""
            Live Support Request Details:
            --------------------------
            Name: {name}
            Email: {email}
            Query: {query}
            
            This message was sent from the PTU Chatbot live support system.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Log SMTP connection attempt
            logger.info("Attempting to connect to SMTP server...")
            
            # Send email
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
            logger.info("SMTP TLS started, attempting login...")
            server.login(EMAIL_USER, EMAIL_PASS)
            logger.info("SMTP login successful, sending email...")
            server.send_message(msg)
            logger.info(f"Email sent successfully to {', '.join(ADMIN_EMAILS)}")
            server.quit()
            
            return jsonify({
                'success': True,
                'message': 'आपका संदेश सफलतापूर्वक भेज दिया गया है! हम जल्द ही आपसे संपर्क करेंगे।'
            })
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Email authentication failed. Please check your email credentials.'
            })
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error sending email. Please try again later.'
            })
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'An unexpected error occurred. Please try again later.'
            })
            
    except Exception as e:
        logger.error(f"Error in live support endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred. Please try again later.'
        })

@app.route('/get_chat_history')
def get_chat_history():
    try:
        chat_history = session.get('chat_history', [])
        current_time = datetime.now()
        
        # Filter out messages older than 7 days
        chat_history = [msg for msg in chat_history 
                       if (current_time - datetime.strptime(msg['timestamp'], "%Y-%m-%d %H:%M:%S")) <= timedelta(days=7)]
        
        # Update session with filtered history
        session['chat_history'] = chat_history
        
        return jsonify({'history': chat_history})
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return jsonify({'history': []})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    try:
        # Don't clear the chat history, just return success
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error in new_chat endpoint: {str(e)}")
        return jsonify({'success': False})

@app.route('/download/<doc_type>/<course>')
def download_document(doc_type, course):
    try:
        # Get the PDF path from utils
        pdf_path = ptu_utils.get_pdf_path(doc_type, course)
        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True)
        return "File not found", 404
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return "Error downloading file", 500

if __name__ == '__main__':
    print("\nStarting chatbot server...")
    print("Access the chatbot at http://localhost:5000")
    app.run(debug=True)
