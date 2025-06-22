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
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
from utils import PTUUtils
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session
ptu_utils = PTUUtils()

# Store chat history in memory
chat_histories = {}

# Initialize empty DataFrame and responses
df = pd.DataFrame()
responses = {}
vectorizer = None
question_vectors = None

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USERNAME = "your-email@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "your-app-password"     # Replace with your app password
SUPPORT_EMAIL = "support@ptu.ac.in"      # Replace with support email

# Try to load data files
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
        print("Sample data from CSV:")
        print(df.head())
    else:
        print(f"Error: CSV file not found at {csv_path}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Directory contents: {os.listdir('.')}")
    
    # Load responses JSON if exists
    json_path = 'data/responses.json'
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            responses = json.load(f)
            print("Successfully loaded responses JSON")
            print(f"Number of responses: {len(responses)}")
    else:
        print(f"Error: JSON file not found at {json_path}")
        print(f"Directory contents of data/: {os.listdir('data') if os.path.exists('data') else 'data directory not found'}")

    # Load intents JSON if exists
    intents_path = 'data/intents.json'
    intents = []
    if os.path.exists(intents_path):
        with open(intents_path, 'r', encoding='utf-8') as f:
            intents_data = json.load(f)
            intents = intents_data.get('intents', [])
            print("Successfully loaded intents JSON")
            print(f"Number of intents: {len(intents)}")
    else:
        print(f"Error: Intents JSON file not found at {intents_path}")

except Exception as e:
    print(f"Error loading data files: {str(e)}")
    print(f"Exception type: {type(e)}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")

def clean_text(text):
    # Convert to lowercase and remove extra spaces
    text = str(text).lower().strip()
    # Remove punctuation except question marks
    text = re.sub(r'[^\w\s?]', '', text)
    return text

def find_best_match(user_message, questions):
    if vectorizer is None or question_vectors is None:
        print("Vectorizer or question vectors not initialized")
        return -1
        
    # Clean and vectorize user message
    user_message = clean_text(user_message)
    user_vector = vectorizer.transform([user_message])
    
    # Calculate cosine similarity
    similarities = cosine_similarity(user_vector, question_vectors).flatten()
    best_match_idx = similarities.argmax()
    best_similarity = similarities[best_match_idx]
    
    print(f"Best similarity score: {best_similarity:.3f}")
    
    # Return best match if similarity is above threshold
    if best_similarity > 0.4:  # Increased threshold from 0.3 to 0.4
        return best_match_idx
    
    return -1

def get_intent_response(user_message):
    user_message = user_message.lower()
    user_tokens = set(re.findall(r'\w+', user_message))
    best_match = None
    best_score = 0
    
    print(f"User tokens: {user_tokens}")
    
    for intent in intents:
        for pattern in intent.get('patterns', []):
            pattern_tokens = set(re.findall(r'\w+', pattern.lower()))
            if not pattern_tokens:
                continue
            common_tokens = user_tokens & pattern_tokens
            score = len(common_tokens) / len(pattern_tokens)
            print(f"Pattern: {pattern}, Score: {score:.3f}")
            
            if score > best_score and score >= 0.5:  # Reduced threshold from 0.6 to 0.5
                best_score = score
                best_match = intent
    
    if best_match:
        print(f"Found intent match with score: {best_score:.3f}")
        return random.choice(best_match.get('responses', []))
    
    print("No intent match found")
    return None

def get_bot_response(user_message):
    try:
        if not user_message:
            return "Please enter a message."
        
        message_lower = user_message.lower().strip()
        print(f"\nProcessing message: {message_lower}")
        
        # Check for document requests
        if any(word in message_lower for word in ["fee", "fees"]):
            for course in ["btech", "mtech", "mba"]:
                if course in message_lower:
                    response = ptu_utils.get_document_response("fee_structure", course)
                    print(f"Found fee structure response for {course}")
                    return response
        
        if any(word in message_lower for word in ["timetable", "time table"]):
            for course in ["btech", "mtech", "mba"]:
                if course in message_lower:
                    response = ptu_utils.get_document_response("timetable", course)
                    print(f"Found timetable response for {course}")
                    return response
        
        if "syllabus" in message_lower:
            for course in ["btech", "mtech", "mba"]:
                if course in message_lower:
                    response = ptu_utils.get_document_response("syllabus", course)
                    print(f"Found syllabus response for {course}")
                    return response
        
        # Check for notice requests
        if any(word in message_lower for word in ["notice", "notices", "notification"]):
            notices = ptu_utils.get_notices()
            response = ptu_utils.format_notice_response(notices)
            print("Found notice response")
            return response
        
        # Check basic responses from JSON
        if responses:
            for pattern, response in responses.items():
                if pattern.lower() in message_lower:
                    print(f"Found matching pattern in responses.json: {pattern}")
                    return response
        
        # Check intents.json
        intent_response = get_intent_response(user_message)
        if intent_response:
            print("Found matching intent")
            return intent_response
        
        # Check CSV data if available
        if not df.empty:
            questions = df['User Query (Pattern)'].tolist()
            best_match_idx = find_best_match(message_lower, questions)
            
            if best_match_idx != -1:
                matched_question = questions[best_match_idx]
                print(f"Found match in CSV: '{matched_question}' for query: '{message_lower}'")
                return df.iloc[best_match_idx]['Bot Response']
            else:
                print("No good match found in CSV data")
        else:
            print("CSV data is empty")
        
        print("No matching response found")
        return "I apologize, but I don't have specific information about that. Please try rephrasing your question or ask something else."
        
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return "I'm having trouble processing your request. Please try again."

@app.route('/')
def home():
    if 'user_id' not in session:
        session['user_id'] = str(random.randint(1000, 9999))
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_id = session.get('user_id', str(random.randint(1000, 9999)))
        user_message = request.json.get('message', '').strip()
        
        if not user_message:
            return jsonify({'response': 'Please enter a message.'})
        
        # Initialize chat history for new users
        if user_id not in chat_histories:
            chat_histories[user_id] = []
        
        # Get bot response
        response = get_bot_response(user_message)
        
        # Save to chat history
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_histories[user_id].append({
            'timestamp': timestamp,
            'user_message': user_message,
            'bot_response': response
        })
        
        return jsonify({'response': response})
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'response': 'An error occurred. Please try again.'})

@app.route('/get_chat_history')
def get_chat_history():
    try:
        user_id = session.get('user_id')
        if not user_id or user_id not in chat_histories:
            return jsonify({'history': []})
        return jsonify({'history': chat_histories[user_id]})
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        return jsonify({'history': []})

@app.route('/clear_chat_history')
def clear_chat_history():
    try:
        user_id = session.get('user_id')
        if user_id and user_id in chat_histories:
            chat_histories[user_id] = []
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error clearing chat history: {str(e)}")
        return jsonify({'success': False})

@app.route('/download/<doc_type>/<course>')
def download_document(doc_type, course):
    try:
        pdf_path = ptu_utils.get_pdf_path(doc_type, course)
        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True)
        return "File not found", 404
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return "Error downloading file", 500

@app.route('/new_chat', methods=['POST'])
def new_chat():
    try:
        user_id = session.get('user_id')
        if user_id:
            chat_histories[user_id] = []
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error creating new chat: {str(e)}")
        return jsonify({'success': False})

@app.route('/send_support_email', methods=['POST'])
def send_support_email():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        query = data.get('query')
        
        if not all([name, email, query]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USERNAME
        msg['To'] = SUPPORT_EMAIL
        msg['Subject'] = f"Support Request from {name}"
        
        body = f"""
        Name: {name}
        Email: {email}
        Query: {query}
        
        This is an automated message from the PTU Chatbot support system.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return jsonify({'success': True, 'message': 'Email sent successfully'})
        
    except Exception as e:
        print(f"Error sending support email: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to send email'})

if __name__ == '__main__':
    print("\nStarting chatbot server...")
    print("Access the chatbot at http://localhost:5000")
    app.run(debug=True)