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
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "student_portal.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'profile_photos')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = '@gmail.com'

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

mail = Mail(app)

# Password reset token serializer
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
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
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SupportTicket(db.Model):
    __tablename__ = 'support_ticket'
    
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
        filename = secure_filename(f"{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
        
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

@app.route('/clear_chat_history', methods=['POST'])
@login_required
def clear_chat_history():
    try:
        ChatHistory.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<doc_type>/<course>')
@login_required
def download_document(doc_type, course):
    file_path = ptu_utils.get_pdf_path(doc_type, course)
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/get_notices')
@login_required
def get_notices():
    try:
        notices = ptu_utils.get_notices()
        return jsonify({'notices': notices})
    except Exception as e:
        return jsonify({'notices': [], 'error': str(e)})

@app.route('/send_support_email', methods=['POST'])
def send_support_email():
    try:
        data = request.get_json()
        name = data.get('name', 'Anonymous')
        email = data.get('email', 'No email')
        message = data.get('message', '')
        subject = data.get('subject', 'PTU Support Request')

        # Email content
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

        msg = Message(subject=subject, recipients=['vkviki0786@gmail.com'], body=body)
        mail.send(msg)
        return jsonify({'success': True, 'info': 'Support email sent!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/live_support', methods=['POST'])
def live_support():
    try:
        # Get JSON data from the request
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        query = data.get('query')
        
        # Validate required fields
        if not all([name, email, query]):
            return jsonify({
                'success': False,
                'message': 'Please fill in all required fields.'
            })
        
        # Create email content
        subject = f"Live Support Request from {name}"
        body = f"""
Live Support Request Details:
--------------------------
Name: {name}
Email: {email}
Query: {query}

This message was sent from the PTU Chatbot live support system.
        """
        
        # Send email to admin
        msg = Message(subject=subject, recipients=['vkviki0786@gmail.com'], body=body)
        mail.send(msg)
        
        return jsonify({
            'success': True,
            'message': 'Your message has been sent successfully! We will contact you soon.'
        })
        
    except Exception as e:
        print(f"Error in live support: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while sending your message. Please try again.'
        })

@app.route('/course_materials')
@login_required
def course_materials():
    streams = [
        "Computer Science Engineering",
        "Information Technology",
        "Electronics & Communication Engineering",
        "Mechanical Engineering",
        "Civil Engineering",
        "Electrical Engineering",
        "Chemical Engineering",
        "Biotechnology",
        "Automobile Engineering",
        "Aerospace Engineering",
        "Food Technology",
        "Textile Engineering",
        "Others"
    ]
    return render_template('course_materials.html', streams=streams)

@app.route('/course_materials/<stream>')
@login_required
def show_notes(stream):
    # Dummy notes data; replace with real data as needed
    notes = [
        {"title": "Unit 1 Notes", "file": "unit1.pdf"},
        {"title": "Unit 2 Notes", "file": "unit2.pdf"}
    ]
    return render_template('notes.html', stream=stream, notes=notes)

@app.route('/faqs')
def faqs():
    return render_template('faqs.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('PTU Student Portal Password Reset', recipients=[user.email])
            msg.body = f"""
Hello {user.full_name},

To reset your password, click the link below:
{reset_url}

If you did not request this, please ignore this email.

Regards,
PTU Student Support Team
"""
            try:
                mail.send(msg)
                flash('A password reset link has been sent to your email.', 'success')
            except Exception as e:
                flash('Error sending email. Please try again later.', 'danger')
        else:
            flash('No account found with that email address.', 'danger')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Invalid user.', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if not password or password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(request.url)
        user.password = generate_password_hash(password)
        db.session.commit()
        flash('Your password has been reset. You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
