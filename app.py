from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import pytz
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import requests
from bs4 import BeautifulSoup
from chatbot.chatbot import get_bot_response
from chatbot.ptu_utils import PTUUtils

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "student_portal.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'profile_photos')

# Database initialize
db = SQLAlchemy(app)

# Create tables inside app context
with app.app_context():
    db.create_all()

# Set timezone
timezone = pytz.timezone('Asia/Kolkata')

# Configure scheduler with timezone
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler(timezone=timezone)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    _tablename_ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    enrollment_number = db.Column(db.String(20), unique=True, nullable=False)
    profile_photo = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tickets = db.relationship('SupportTicket', backref='user', lazy=True)

    def get_profile_photo_url(self):
        if self.profile_photo:
            return url_for('static', filename=f'profile_photos/{self.profile_photo}')
        return None

class Admin(UserMixin, db.Model):
    _tablename_ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SupportTicket(db.Model):
    _tablename_ = 'support_ticket'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    archived = db.Column(db.Boolean, default=False)
    archived_at = db.Column(db.DateTime, nullable=True)
    starred = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'deleted': self.deleted,
            'archived': self.archived,
            'starred': self.starred
        }

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)
    link = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return user
    return Admin.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        course = request.form.get('course')
        semester = request.form.get('semester')
        enrollment_number = request.form.get('enrollment_number')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            full_name=full_name,
            course=course,
            semester=semester,
            enrollment_number=enrollment_number
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error during registration. Please try again.', 'error')
    
    return render_template('register.html')
@app.route("/forgot_password")
def forgot_password():
    return "Forgot Password functionality coming soon..."
    
@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch latest notices
    notices = Notice.query.order_by(Notice.date_posted.desc()).limit(10).all()
    return render_template('dashboard.html', notices=notices)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update user profile
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.email = request.form.get('email', current_user.email)
        current_user.course = request.form.get('course', current_user.course)
        current_user.semester = request.form.get('semester', current_user.semester)
        current_user.enrollment_number = request.form.get('enrollment_number', current_user.enrollment_number)
        
        # Handle password change if provided
        new_password = request.form.get('new_password')
        if new_password:
            current_user.password = generate_password_hash(new_password)
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error updating profile. Please try again.', 'error')
        
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

@app.route('/support_tickets', methods=['GET', 'POST'])
@login_required
def support_tickets():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            subject = request.form.get('subject')
            message = request.form.get('message')
            
            if not subject or not message:
                flash('Please fill in all fields', 'error')
                return redirect(url_for('support_tickets'))
            
            ticket = SupportTicket(
                user_id=current_user.id,
                subject=subject,
                message=message
            )
            
            try:
                db.session.add(ticket)
                db.session.commit()
                flash('Query created successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error creating query. Please try again.', 'error')
            
            return redirect(url_for('support_tickets'))
    
    # Get queries based on view type
    view = request.args.get('view', 'inbox')
    
    if view == 'trash':
        tickets = SupportTicket.query.filter_by(
            user_id=current_user.id,
            deleted=True
        ).order_by(SupportTicket.deleted_at.desc()).all()
    elif view == 'archive':
        tickets = SupportTicket.query.filter_by(
            user_id=current_user.id,
            archived=True,
            deleted=False
        ).order_by(SupportTicket.archived_at.desc()).all()
    elif view == 'starred':
        tickets = SupportTicket.query.filter_by(
            user_id=current_user.id,
            starred=True,
            deleted=False,
            archived=False
        ).order_by(SupportTicket.created_at.desc()).all()
    else:  # inbox
        tickets = SupportTicket.query.filter_by(
            user_id=current_user.id,
            deleted=False,
            archived=False
        ).order_by(SupportTicket.created_at.desc()).all()
    
    return render_template('support_tickets.html', tickets=tickets, view=view)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        data = request.get_json()
        message = data.get('message', '')
        if message:
            # Use chatbot's AI logic
            response = get_bot_response(message)
            # Save chat history in DB (as before)
            chat_history = ChatHistory(
                user_id=current_user.id,
                message=message,
                response=response,
                timestamp=datetime.utcnow()
            )
            db.session.add(chat_history)
            db.session.commit()
            return jsonify({'response': response})
    return render_template('chat.html')

@app.route('/upload_profile_photo', methods=['POST'])
@login_required
def upload_profile_photo():
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['photo']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Create a unique filename
        filename = secure_filename(f"{current_user.username}{datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
        
        # Delete old profile photo if it exists
        if current_user.profile_photo:
            old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_photo)
            if os.path.exists(old_photo_path):
                os.remove(old_photo_path)
        
        # Save the new photo
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Update database
        current_user.profile_photo = filename
        db.session.commit()
        
        return jsonify({
            'success': True,
            'photo_url': url_for('static', filename=f'profile_photos/{filename}')
        })
    
    return jsonify({'success': False, 'error': 'Invalid file type'}), 400

def process_message(message):
    # Simple response logic - can be enhanced with more sophisticated NLP
    message = message.lower()
    
    if any(word in message for word in ['hello', 'hi', 'hey']):
        return "Hello! How can I help you today?"
    elif any(word in message for word in ['admission', 'apply', 'enroll']):
        return "For admission queries, please visit the admissions office or check our website at www.ptu.ac.in"
    elif any(word in message for word in ['fee', 'payment', 'tuition']):
        return "You can find fee details and payment options on the university portal. Need help accessing it?"
    elif any(word in message for word in ['exam', 'schedule', 'result']):
        return "Exam schedules and results are available on the university portal. Would you like me to guide you there?"
    elif any(word in message for word in ['syllabus', 'course', 'curriculum']):
        return "Course syllabi are available in the academics section. Which course are you looking for?"
    elif any(word in message for word in ['library', 'book', 'resource']):
        return "The university library is open from 9 AM to 5 PM. You can access digital resources through the library portal."
    elif any(word in message for word in ['hostel', 'accommodation', 'room']):
        return "Hostel applications are processed through the accommodation office. Would you like their contact details?"
    elif any(word in message for word in ['scholarship', 'financial aid', 'grant']):
        return "Information about scholarships and financial aid is available on the student welfare section of our website."
    elif any(word in message for word in ['thank', 'thanks']):
        return "You're welcome! Is there anything else I can help you with?"
    else:
        return "I'm not sure I understand. Could you please rephrase your question or try asking about admissions, fees, exams, or other university services?"

def fetch_ptu_notices():
    try:
        # Fetch the webpage content
        url = 'https://ptu.ac.in/noticeboard-main/'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the notice table
        notice_table = soup.find('table')
        if not notice_table:
            print("No notice table found")
            return []
        
        notices = []
        rows = notice_table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                title = cols[0].text.strip()
                date_str = cols[1].text.strip()
                link = cols[2].find('a')['href'] if cols[2].find('a') else None
                
                if title and date_str:
                    try:
                        # Convert date string to datetime object
                        date_posted = datetime.strptime(date_str, '%d/%m/%Y')
                        
                        # Check if notice already exists
                        existing_notice = Notice.query.filter_by(title=title).first()
                        if not existing_notice:
                            notice = Notice(
                                title=title,
                                date_posted=date_posted,
                                link=link
                            )
                            notices.append(notice)
                    except ValueError as e:
                        print(f"Error parsing date {date_str}: {e}")
                        continue
        
        if notices:
            try:
                db.session.bulk_save_objects(notices)
                db.session.commit()
                print(f"Added {len(notices)} new notices")
            except Exception as e:
                print(f"Error saving notices: {e}")
                db.session.rollback()
        
        return notices
    except Exception as e:
        print(f"Error fetching notices: {e}")
        return []

# Add scheduler to fetch notices periodically
scheduler.add_job(func=fetch_ptu_notices, trigger="interval", hours=6)
scheduler.start()

@app.route('/delete_query', methods=['POST'])
@login_required
def delete_query():
    data = request.get_json()
    query_id = data.get('query_id')
    permanent = data.get('permanent', False)
    
    ticket = SupportTicket.query.get(query_id)
    if ticket and ticket.user_id == current_user.id:
        if permanent:
            db.session.delete(ticket)
        else:
            ticket.deleted = True
            ticket.deleted_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Query not found'}), 404

@app.route('/archive_query', methods=['POST'])
@login_required
def archive_query():
    data = request.get_json()
    query_id = data.get('query_id')
    
    ticket = SupportTicket.query.get(query_id)
    if ticket and ticket.user_id == current_user.id:
        ticket.archived = True
        ticket.archived_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Query not found'}), 404

@app.route('/toggle_star', methods=['POST'])
@login_required
def toggle_star():
    data = request.get_json()
    query_id = data.get('query_id')
    
    ticket = SupportTicket.query.get(query_id)
    if ticket and ticket.user_id == current_user.id:
        ticket.starred = not ticket.starred
        
        try:
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': False, 'error': 'Query not found'}), 404

@app.route('/refresh_queries')
@login_required
def refresh_queries():
    try:
        # Get fresh data
        tickets = SupportTicket.query.filter_by(
            user_id=current_user.id,
            deleted=False,
            archived=False
        ).order_by(SupportTicket.created_at.desc()).all()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/notices')
@login_required
def notices():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    notices = Notice.query.order_by(Notice.date_posted.desc()).paginate(page=page, per_page=per_page)
    return render_template('notices.html', notices=notices)

@app.route('/refresh_notices')
@login_required
def refresh_notices():
    try:
        new_notices = fetch_ptu_notices()
        if new_notices:
            flash(f'Successfully added {len(new_notices)} new notices!', 'success')
        else:
            flash('No new notices found.', 'info')
    except Exception as e:
        flash(f'Error refreshing notices: {str(e)}', 'error')
    
    return redirect(url_for('notices'))

def add_column(engine, table_name, column):
    column_name = column.compile(dialect=engine.dialect)
    column_type = column.type.compile(engine.dialect)
    engine.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')

@app.template_filter('now')
def current_year(format_string):
    return datetime.now().strftime(format_string)

ptu_utils = PTUUtils()

@app.route('/get_chat_history')
@login_required
def get_chat_history():
    try:
        history = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp).all()
        chat_list = [
            {
                'timestamp': chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'user_message': chat.message,
                'bot_response': chat.response
            } for chat in history
        ]
        return jsonify({'history': chat_list})
    except Exception as e:
        return jsonify({'history': [], 'error': str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
