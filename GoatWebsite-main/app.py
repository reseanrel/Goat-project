from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import os

import psycopg2
import psycopg2.extras

# Database connection
db = psycopg2.connect(
    host="db.grxqzspccuhzivpiffup.supabase.co",      # your Supabase host
    dbname="postgres",                 # or your custom DB name
    user="postgres",                   # or your Supabase DB user
    password="04131616qQ@@@...",
    port="5432"
)

# Enables dict-like access (just like dictionary=True in MySQL)
cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'pila-pets-week1-secret-key'

admin = []
users = []
pets = []
vaccinations = []
next_pet_id = 1
next_user_id = 1
next_vaccination_id = 1

#demo acc lang
default_admin = {
    'id': next_user_id,
    'full_name': 'Sir John Mark P',
    'email': 'admin@pila.pets',
    'password': 'asdf',
    'is_admin': True,
    'contact_number': '09123456789',
    'address': 'Pila, Laguna',
    'age': 35,
    'created_at': datetime.now()
}
admin.append(default_admin)
next_user_id += 1


sample_users = [
    {
        'id': next_user_id,
        'full_name': 'Frandie wewets',
        'email': 'frandiekaivin@gmail.com',
        'password': 'asdf',
        'is_admin': False,
        'contact_number': '09123456780',
        'address': 'jan lang',
        'age': 28,
        'created_at': datetime.now()
    }
]
users.extend(sample_users)
next_user_id += 1


sample_pets = [
    {
        'id': next_pet_id,
        'name': 'Buddy',
        'category': 'Dog',
        'pet_type': 'Aspin',
        'age': 3,
        'color': 'Brown',
        'gender': 'Male',
        'owner_id': 2,  # Frandie Kaivin Colderia
        'registered_on': datetime.now(),
        'photo_url': None
    },
    {
        'id': next_pet_id + 1,
        'name': 'Mimi',
        'category': 'Cat',
        'pet_type': 'Persian',
        'age': 2,
        'color': 'White',
        'gender': 'Female',
        'owner_id': 2,  # Frandie Kaivin Colderia
        'registered_on': datetime.now(),
        'photo_url': None
    }
]
pets.extend(sample_pets)
next_pet_id += 2

# Authentication Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # ✅ Fetch user from MySQL
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user and email == 'admin@pila.pets' and password == 'asdf':
            user = {
                'id': 0,
                'full_name': 'Administrator',
                'email': email,
                'password': password,
                'is_admin': True,
                'contact_number': 'N/A',
                'address': 'Pila, Laguna',
                'age': 30
            }

        if user and user['password'] == password:
            # ✅ Save user info in session
            session['user_id'] = user['id']
            session['is_admin'] = user['is_admin']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            session['user_contact'] = user.get('contact_number', '')
            session['user_address'] = user.get('address', '')
            session['user_age'] = user.get('age', '')

            if user['is_admin']:
                flash('Welcome back, Administrator!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash(f'Welcome back, {user["full_name"].split()[0]}!', 'success')
                return redirect(url_for('user_dashboard'))

        else:
            flash('Invalid email or password', 'error')

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        contact_number = request.form.get('contact_number')
        address = request.form.get('address')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([full_name, email, password, confirm_password]):
            flash('Please fill all required fields', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')

        try:
            # ✅ Check for duplicate email in the database
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()
            if existing_user:
                flash('Email already registered', 'error')
                return render_template('auth/register.html')

            # ✅ Insert new user into MySQL
            cursor.execute("""
                INSERT INTO users (full_name, age, contact_number, address, email, password, is_admin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (full_name, age, contact_number, address, email, password, False))
            db.commit()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            print("❌ ERROR:", e)  # 👈 will show actual MySQL or logic error in the terminal
            db.rollback()
            flash('An error occurred during registration. Please try again.', 'error')

    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to get user by ID
def get_user_by_id(user_id):
    return next((u for u in users if u['id'] == user_id), None)

# User Routes
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    cursor.execute("SELECT * FROM pets WHERE owner_id = %s", (session['user_id'],))
    user_pets = cursor.fetchall()
    
    return render_template('user/dashboard.html', 
                         user_pets=user_pets,
                         user_name=session['user_name'],
                         user_email=session['user_email'],
                         user_contact=session['user_contact'],
                         user_address=session['user_address'])

@app.route('/user/my-pets')
@login_required
def my_pets():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    cursor.execute("SELECT * FROM pets WHERE owner_id = %s", (session['user_id'],))
    user_pets = cursor.fetchall()
    
    return render_template('user/my_pets.html', 
                         pets=user_pets,
                         user_name=session['user_name'],
                         user_email=session['user_email'],
                         user_contact=session['user_contact'],
                         user_address=session['user_address'])

@app.route('/user/register-pet', methods=['GET', 'POST'])
@login_required
def register_pet():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('pet_name')
        category = request.form.get('pet_category')
        pet_type = request.form.get('pet_type')
        age = request.form.get('age')
        color = request.form.get('color')
        gender = request.form.get('gender')
        
        if not name or not category:
            flash('Pet name and category are required', 'error')
            return render_template('user/register_pet.html')
        
        global next_pet_id
        new_pet = {
            'id': next_pet_id,
            'name': name,
            'category': category,
            'pet_type': pet_type,
            'age': int(age) if age and age.isdigit() else None,
            'color': color,
            'gender': gender,
            'owner_id': session['user_id'],
            'registered_on': datetime.now(),
            'photo_url': None
        }
        cursor.execute("""
            INSERT INTO pets (name, category, pet_type, age, color, gender, owner_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, category, pet_type, age, color, gender, session['user_id']))
        db.commit()
        
        flash(f'Pet "{name}" registered successfully!', 'success')
        return redirect(url_for('my_pets'))
    
    return render_template('user/register_pet.html')

@app.route('/user/pet/<int:pet_id>')
@login_required
def pet_details(pet_id):
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    cursor.execute("SELECT * FROM pets WHERE id = %s AND owner_id = %s", (pet_id, session['user_id']))
    pet = cursor.fetchone()
    
    if not pet or pet['owner_id'] != session['user_id']:
        flash('Access denied', 'error')
        return redirect(url_for('my_pets'))
    
    # Get owner info from session
    owner_info = {
        'full_name': session['user_name'],
        'email': session['user_email'],
        'contact_number': session['user_contact'],
        'address': session['user_address']
    }
    
    return render_template('user/pet_details.html', pet=pet, owner=owner_info)

@app.route('/user/pet/<int:pet_id>/vaccinations')
@login_required
def vaccination_records(pet_id):
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    
    pet = next((p for p in pets if p['id'] == pet_id), None)
    
    if not pet or pet['owner_id'] != session['user_id']:
        flash('Access denied', 'error')
        return redirect(url_for('my_pets'))
    
    pet_vaccinations = [v for v in vaccinations if v['pet_id'] == pet_id]
    
    return render_template('user/vaccination.html', pet=pet, vaccinations=pet_vaccinations)

@app.route('/user/add-vaccination/<int:pet_id>', methods=['POST'])
@login_required
def add_vaccination(pet_id):
    if session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Access denied'})
    
    pet = next((p for p in pets if p['id'] == pet_id), None)
    if not pet or pet['owner_id'] != session['user_id']:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    vaccine_name = request.form.get('vaccine_name')
    date_administered = request.form.get('date_administered')
    next_due_date = request.form.get('next_due_date')
    administered_by = request.form.get('administered_by')
    notes = request.form.get('notes')
    
    if not vaccine_name or not date_administered:
        return jsonify({'success': False, 'message': 'Vaccine name and date are required'})
    
    global next_vaccination_id
    new_vaccination = {
        'id': next_vaccination_id,
        'vaccine_name': vaccine_name,
        'date_administered': datetime.strptime(date_administered, '%Y-%m-%d'),
        'next_due_date': datetime.strptime(next_due_date, '%Y-%m-%d') if next_due_date else None,
        'administered_by': administered_by,
        'notes': notes,
        'pet_id': pet_id
    }
    vaccinations.append(new_vaccination)
    next_vaccination_id += 1
    
    return jsonify({'success': True, 'message': 'Vaccination record added successfully'})

# Admin Routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    cursor.execute("SELECT COUNT(*) AS total FROM pets")
    total_pets = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM pets WHERE category = 'Dog'")
    dogs = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM pets WHERE category = 'Cat'")
    cats = cursor.fetchone()['total']

    other_pets = total_pets - dogs - cats
    
    # Get recent pets with owner information
    recent_pets_with_owners = []
    for pet in sorted(pets, key=lambda x: x['registered_on'], reverse=True)[:5]:
        owner = get_user_by_id(pet['owner_id'])
        pet_with_owner = pet.copy()
        pet_with_owner['owner_name'] = owner['full_name'] if owner else 'Unknown Owner'
        recent_pets_with_owners.append(pet_with_owner)
    
    return render_template('admin/dashboard.html', 
                         total_pets=total_pets,
                         dogs=dogs,
                         cats=cats,
                         other_pets=other_pets,
                         pets=recent_pets_with_owners)

@app.route('/admin/pets')
@login_required
@admin_required
def admin_pets():
    # Get all pets with owner information
    cursor.execute("""
        SELECT pets.*, users.full_name AS owner_name, users.email AS owner_email,
            users.contact_number AS owner_contact, users.address AS owner_address
        FROM pets
        JOIN users ON pets.owner_id = users.id
    """)
    pets_with_owners = cursor.fetchall()
    
    return render_template('admin/pets.html', pets=pets_with_owners)

if __name__ == '__main__':
    app.run(debug=True)