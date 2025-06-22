from flask import Flask, render_template, request, jsonify, send_file, session
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
import os
import re
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# PDF configuration
PDF_DIRECTORY = 'static/pdfs'
os.makedirs(PDF_DIRECTORY, exist_ok=True)

PDF_FILES = {
    'fee_structure': {
        'btech': 'btech_fees.pdf',
        'mtech': 'mtech_fees.pdf',
        'mba': 'mba_fees.pdf'
    },
    'timetable': {
        'btech': 'btech_timetable.pdf',
        'mtech': 'mtech_timetable.pdf',
        'mba': 'mba_timetable.pdf'
    },
    'syllabus': {
        'btech': 'btech_syllabus.pdf',
        'mtech': 'mtech_syllabus.pdf',
        'mba': 'mba_syllabus.pdf'
    }
}

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'vkviki0786@gmail.com'
EMAIL_PASS = 'odsj fedp tznu inhx'
ADMIN_EMAILS = ['miss.vanshika.sharma.10@gmail.com', 'vkviki0786@gmail.com']

class Chatbot:
    def __init__(self):
        self.df = None
        self.responses = {}
        self.vectorizer = None
        self.question_vectors = None
        self.load_data()

    def load_data(self):
        try:
            # Load CSV file
            csv_path = 'Structured_Chatbot_Data    chatbot csv.csv'
            if os.path.exists(csv_path):
                self.df = pd.read_csv(csv_path, encoding='utf-8')
                # Clean the data
                self.df['User Query (Pattern)'] = self.df['User Query (Pattern)'].fillna('')
                self.df['Bot Response'] = self.df['Bot Response'].fillna('')
                self.df['User Query (Pattern)'] = self.df['User Query (Pattern)'].astype(str)
                self.df['Bot Response'] = self.df['Bot Response'].astype(str)
                
                # Initialize TF-IDF vectorizer
                self.vectorizer = TfidfVectorizer()
                self.question_vectors = self.vectorizer.fit_transform(self.df['User Query (Pattern)'])
                
                print(f"Successfully loaded CSV file with {len(self.df)} rows")
            else:
                print(f"Warning: CSV file not found at {csv_path}")
            
            # Load responses JSON if exists
            json_path = 'data/responses.json'
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.responses = json.load(f)
                    print("Successfully loaded responses JSON")
            else:
                print(f"Warning: JSON file not found at {json_path}")
                
        except Exception as e:
            print(f"Error loading data: {str(e)}")

    def clean_text(self, text):
        # Convert to lowercase and remove extra spaces
        text = str(text).lower().strip()
        # Remove punctuation except question marks
        text = re.sub(r'[^\w\s?]', '', text)
        return text

    def find_best_match(self, user_message):
        if self.vectorizer is None or self.question_vectors is None:
            return None, -1
            
        # Clean and vectorize user message
        user_message = self.clean_text(user_message)
        user_vector = self.vectorizer.transform([user_message])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(user_vector, self.question_vectors).flatten()
        best_match_idx = similarities.argmax()
        
        # Return best match if similarity is above threshold
        if similarities[best_match_idx] > 0.3:
            return self.df.iloc[best_match_idx]['Bot Response'], similarities[best_match_idx]
            
        return None, -1

    def get_response(self, user_message):
        try:
            if not user_message:
                return "Please enter a message."
                
            message_lower = user_message.lower().strip()
            
            # Check basic responses from JSON
            if self.responses:
                for pattern, response in self.responses.items():
                    if pattern.lower() in message_lower:
                        return response
            
            # Find best match from CSV data
            best_response, similarity = self.find_best_match(message_lower)
            if best_response is not None:
                return best_response
            
            return "I apologize, but I don't have specific information about that. Please try rephrasing your question or ask something else."
            
        except Exception as e:
            logger.error(f"Error getting response: {str(e)}")
            return "I'm having trouble processing your request. Please try again."

def get_pdf_path(doc_type, course):
    if doc_type in PDF_FILES and course in PDF_FILES[doc_type]:
        return os.path.join(PDF_DIRECTORY, PDF_FILES[doc_type][course])
    return None

@app.route('/')
def home():
    if 'chat_history' not in session:
        session['chat_history'] = []
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
            
        # Get bot response
        bot = Chatbot()
        bot_response = bot.get_response(user_message)
        
        # Update chat history
        chat_history = session.get('chat_history', [])
        chat_history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'user_message': user_message,
            'bot_response': bot_response
        })
        session['chat_history'] = chat_history
        
        return jsonify({'response': bot_response})
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your message'}), 500

@app.route('/download/<doc_type>/<course>')
def download_pdf(doc_type, course):
    try:
        pdf_path = get_pdf_path(doc_type, course)
        if pdf_path and os.path.exists(pdf_path):
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f"{course}_{doc_type}.pdf",
                mimetype='application/pdf'
            )
        logger.error(f"PDF not found: {pdf_path}")
        return "PDF file not found", 404
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        return "Error downloading file", 500

@app.route('/get_chat_history')
def get_chat_history():
    try:
        chat_history = session.get('chat_history', [])
        return jsonify({'history': chat_history})
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return jsonify({'history': []})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    try:
        session['chat_history'] = []
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error in new_chat endpoint: {str(e)}")
        return jsonify({'success': False})

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
            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
                server.starttls()
                logger.info("SMTP TLS started, attempting login...")
                server.login(EMAIL_USER, EMAIL_PASS)
                logger.info("SMTP login successful, sending email...")
                server.send_message(msg)
                logger.info(f"Email sent successfully to {', '.join(ADMIN_EMAILS)}")
                
            return jsonify({
                'success': True,
                'message': 'आपका संदेश सफलतापूर्वक भेज दिया गया है! हम जल्द ही आपसे संपर्क करेंगे।'
            })
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'ईमेल सर्वर प्रमाणीकरण विफल हुआ। कृपया कुछ देर बाद पुनः प्रयास करें।'
            })
            
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'ईमेल भेजने में विफल। कृपया कुछ देर बाद पुनः प्रयास करें।'
            })
            
    except Exception as e:
        logger.error(f"Live support error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'कोई त्रुटि हुई। कृपया पुनः प्रयास करें।'
        })

if __name__ == '__main__':
    print("\nStarting chatbot server...")
    print("Access the chatbot at http://localhost:5000")
    app.run(debug=True)