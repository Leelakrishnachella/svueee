from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/img/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Sample admin credentials
admin_username = 'krishna'
admin_password = '123'

# Database connection function
def get_db_connection(database):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

# Create a database and a table to store user data
def initialize_users_database():
    conn = get_db_connection('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Create a database and a table to store event data
def initialize_events_database():
    conn = get_db_connection('events.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            event_name TEXT NOT NULL,
            image TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            cost REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Upload event image and return the filename
def upload_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename
    else:
        return None

@app.route('/')
def home():
    conn_events = get_db_connection('events.db')
    cursor_events = conn_events.cursor()
    events = get_events(cursor_events)
    conn_events.close()

    return render_template('home.html', events=events)

@app.route('/user/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']

        conn = get_db_connection('users.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)", (username, password, email, phone))
        conn.commit()
        conn.close()

        return redirect(url_for('user_login'))
    
    return render_template('user_register.html')

# User login route
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user['username']
            return redirect(url_for('user_dashboard'))
    
    return render_template('user_login.html')

# Define a function to retrieve events for a specific user
def get_user_events(username):
    conn_events = get_db_connection('events.db')
    cursor_events = conn_events.cursor()
    cursor_events.execute("SELECT * FROM events WHERE username = ?", (username,))
    events = cursor_events.fetchall()
    conn_events.close()
    return events


# Admin login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == admin_username and password == admin_password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_login.html')

@app.route('/user/dashboard')
def user_dashboard():
    if 'username' in session:
        conn_events = get_db_connection('events.db')
        cursor_events = conn_events.cursor()

        events = get_events(cursor_events)
        conn_events.close()

        return render_template('user_dashboard.html', events=events)
    return redirect(url_for('user_login'))

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' in session:
        conn_events = get_db_connection('events.db')
        cursor_events = conn_events.cursor()

        # Event handling
        if request.method == 'POST':
            if 'create_event' in request.form:
                create_event(cursor_events, conn_events, request)  # Pass conn_events to the function
            elif 'update_event' in request.form:
                update_event(cursor_events, conn_events, request)  # Pass conn_events to the function
            elif 'delete_event' in request.form:
                delete_event(cursor_events, conn_events, request)  # Pass conn_events to the function

        events = get_events(cursor_events)
        conn_events.close()

        users = get_registered_users()  # Get the list of registered users

        return render_template('admin_dashboard.html', events=events, users=users)

    return redirect(url_for('admin_login'))


# Helper function to update an event
def update_event(cursor, conn, request):  # Pass conn to the function
    event_id = request.form['event_id']
    event_name = request.form['event_name']
    image = request.files['image']
    description = request.form['description']
    date = request.form['date']
    time = request.form['time']
    cost = request.form['cost']

    # Only update the image if a new file is provided
    if image.filename:
        image_filename = upload_image(image)
        cursor.execute("UPDATE events SET event_name=?, image=?, description=?, date=?, time=?, cost=? WHERE id=?",
                       (event_name, image_filename, description, date, time, cost, event_id))
        conn.commit()  # Use the provided conn object
    else:
        cursor.execute("UPDATE events SET event_name=?, description=?, date=?, time=?, cost=? WHERE id=?",
                       (event_name, description, date, time, cost, event_id))
        conn.commit()  # Use the provided conn object

# Helper function to delete an event
def delete_event(cursor, conn, request):  # Pass conn to the function
    event_id = request.form['event_id']
    cursor.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()  # Use the provided conn object

# Helper function to create an event
def create_event(cursor, conn, request):  # Pass conn to the function
    event_name = request.form['event_name']
    image = upload_image(request.files['image'])
    description = request.form['description']
    date = request.form['date']
    time = request.form['time']
    cost = request.form['cost']

    if image:
        cursor.execute("INSERT INTO events (event_name, image, description, date, time, cost) VALUES (?, ?, ?, ?, ?, ?)",
                       (event_name, image, description, date, time, cost))
        conn.commit()  # Use the provided conn object
    else:
        flash('Invalid image format. Allowed formats: .png, .jpg, .jpeg, .gif', 'error')

# Helper function to retrieve events from the database
def get_events(cursor):
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    return events

# Helper function to retrieve registered users from the database
def get_registered_users():
    conn = get_db_connection('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)  # Clear the user's session
    if 'admin' in session:
        session.pop('admin', None)  # Clear the admin session if present
    return redirect(url_for('home'))



if __name__ == '__main__':
    initialize_users_database()
    initialize_events_database()
    app.run(debug=True)
