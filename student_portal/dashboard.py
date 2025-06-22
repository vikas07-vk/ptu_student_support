from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from .models import User, ChatHistory, SupportTicket
from . import db
from datetime import datetime

dashboard = Blueprint('dashboard', __name__)

@dashboard.route('/user/dashboard')
@login_required
def user_dashboard():
    # Get recent chat history
    recent_chats = ChatHistory.query.filter_by(user_id=current_user.id)\
        .order_by(ChatHistory.created_at.desc())\
        .limit(5)\
        .all()
    
    # Get recent support tickets
    recent_tickets = SupportTicket.query.filter_by(user_id=current_user.id)\
        .order_by(SupportTicket.created_at.desc())\
        .limit(5)\
        .all()
    
    return render_template('user_dashboard.html',
                         recent_chats=recent_chats,
                         recent_tickets=recent_tickets)

@dashboard.route('/user/profile')
@login_required
def user_profile():
    return render_template('user_profile.html')

@dashboard.route('/user/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
        current_user.full_name = request.form.get('full_name')
        current_user.course = request.form.get('course')
        current_user.semester = request.form.get('semester')
        current_user.enrollment_number = request.form.get('enrollment_number')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error updating profile. Please try again.', 'error')
    
    return redirect(url_for('dashboard.user_profile'))

@dashboard.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard.user_dashboard'))
    
    # Get statistics
    total_users = User.query.count()
    total_tickets = SupportTicket.query.count()
    open_tickets = SupportTicket.query.filter_by(status='Open').count()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_tickets=total_tickets,
                         open_tickets=open_tickets)

@dashboard.route('/admin/tickets')
@login_required
def admin_tickets():
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard.user_dashboard'))
    
    tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
    return render_template('admin_tickets.html', tickets=tickets)

@dashboard.route('/admin/tickets/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def admin_ticket_detail(ticket_id):
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard.user_dashboard'))
    
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    if request.method == 'POST':
        ticket.status = request.form.get('status')
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Ticket status updated successfully!', 'success')
    
    return render_template('admin_ticket_detail.html', ticket=ticket)

@dashboard.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard.user_dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@dashboard.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied. Admin only.'}), 403
    
    user = User.query.get_or_404(user_id)
    
    try:
        # Delete user's chat history
        ChatHistory.query.filter_by(user_id=user_id).delete()
        
        # Delete user's support tickets
        SupportTicket.query.filter_by(user_id=user_id).delete()
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error deleting user'}), 500

@dashboard.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.course = request.form.get('course')
        user.semester = request.form.get('semester')
        
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
            
        db.session.commit()
        return redirect(url_for('dashboard.user_dashboard'))
        
    return render_template('profile.html', user=user)

@dashboard.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        ticket = SupportTicket(
            user_id=session['user_id'],
            subject=subject,
            message=message
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        return redirect(url_for('dashboard.user_dashboard'))
        
    return render_template('support.html') 