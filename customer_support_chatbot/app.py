import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from chatbot import get_bot_reply

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-development-secret')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'customer_support')
}

def db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access is required.', 'error')
            return redirect(url_for('index'))
        return view(*args, **kwargs)
    return wrapped

def query_one(sql, params=()):
    conn = db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()

def query_all(sql, params=()):
    conn = db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

@app.route('/')
def index():
    return render_template('index.html', user=session.get('name'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not name or not email or len(password) < 8:
            flash('Enter your name, a valid email, and a password of at least 8 characters.', 'error')
            return render_template('register.html')
        conn = db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,%s)',
                        (name, email, generate_password_hash(password), 'customer'))
            conn.commit()
            flash('Account created. Please sign in.', 'success')
            return redirect(url_for('login'))
        except Error:
            conn.rollback()
            flash('Could not create account. That email may already be registered.', 'error')
        finally:
            cur.close(); conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = query_one('SELECT id,name,email,password_hash,role FROM users WHERE email=%s', (email,))
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session.update(user_id=user['id'], name=user['name'], email=user['email'], role=user['role'])
            return redirect(url_for('admin_dashboard' if user['role'] == 'admin' else 'index'))
        flash('Email or password is incorrect.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get('message', '')).strip()
    if not message:
        return jsonify({'reply': 'Please type a message so I can help.'}), 400
    if len(message) > 2000:
        return jsonify({'reply': 'Please keep your message under 2,000 characters.'}), 400
    reply, needs_ticket = get_bot_reply(message)
    ticket_id = None
    if needs_ticket and session.get('user_id'):
        conn = db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO tickets (user_id, subject, description, status) VALUES (%s,%s,%s,%s)',
                        (session['user_id'], message[:120], message, 'Open'))
            conn.commit()
            ticket_id = cur.lastrowid
            reply += f' I created support ticket #{ticket_id} for you.'
        finally:
            cur.close(); conn.close()
    elif needs_ticket:
        reply += ' Sign in first if you want me to create a trackable support ticket.'
    return jsonify({'reply': reply, 'ticket_id': ticket_id})

@app.route('/tickets')
@login_required
def tickets():
    rows = query_all('SELECT id,subject,description,status,admin_reply,created_at FROM tickets WHERE user_id=%s ORDER BY created_at DESC',
                     (session['user_id'],))
    return render_template('tickets.html', tickets=rows)

@app.route('/admin')
@admin_required
def admin_dashboard():
    rows = query_all('SELECT t.id,t.subject,t.description,t.status,t.admin_reply,t.created_at,u.name AS customer_name,u.email FROM tickets t JOIN users u ON t.user_id=u.id ORDER BY t.created_at DESC')
    return render_template('admin.html', tickets=rows)

@app.route('/admin/ticket/<int:ticket_id>', methods=['POST'])
@admin_required
def update_ticket(ticket_id):
    status = request.form.get('status', 'Open')
    reply = request.form.get('admin_reply', '').strip()
    if status not in ('Open', 'In Progress', 'Resolved'):
        flash('Invalid ticket status.', 'error')
        return redirect(url_for('admin_dashboard'))
    conn = db_connection(); cur = conn.cursor()
    try:
        cur.execute('UPDATE tickets SET status=%s, admin_reply=%s WHERE id=%s', (status, reply, ticket_id))
        conn.commit()
        flash(f'Ticket #{ticket_id} updated.', 'success')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(500)
def server_error(_error):
    return render_template('error.html'), 500

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', port=int(os.getenv('PORT', '5001')))
