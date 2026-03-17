from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import random
import string
import plotly.graph_objs as go
import plotly.utils
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bson import ObjectId
import datetime
import os
from dotenv import load_dotenv
import openai
import google.generativeai as genai
import bcrypt
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'uptrack_secret_key_2024_change_in_production')

# Session configuration for persistence
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)  # Sessions last 7 days
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Make datetime available to all templates
@app.context_processor
def inject_datetime():
    return dict(datetime=datetime)

# Initialize session for all requests
@app.before_request
def make_session_permanent():
    session.permanent = True

# Load configuration
try:
    with open('config.json') as f:
        config = json.load(f)['param']
except:
    config = {
        'gmail-user': os.environ.get('GMAIL_USER', ''),
        'gmail-password': os.environ.get('GMAIL_PASSWORD', ''),
        'openai-api-key': os.environ.get('OPENAI_API_KEY', ''),
        'grok-api-key': os.environ.get('GROK_API_KEY', '')
    }

# MongoDB connection with proper error handling
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_CONNECTED = False

def init_database():
    """Initialize MongoDB connection and create indexes"""
    global MONGODB_CONNECTED, client, db, users_collection, activities_collection
    global workouts_collection, meals_collection, goals_collection
    global ai_insights_collection, meal_plans_collection
    
    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        # Test connection
        client.server_info()
        
        db = client['wellnessai_db']
        
        # Collections
        users_collection = db['users']
        activities_collection = db['activities']
        workouts_collection = db['workouts']
        meals_collection = db['meals']
        goals_collection = db['goals']
        ai_insights_collection = db['ai_insights']
        meal_plans_collection = db['meal_plans']
        
        # Create indexes for better performance
        try:
            users_collection.create_index('email', unique=True)
            users_collection.create_index('phone')
            activities_collection.create_index([('user_id', 1), ('date', -1)])
            workouts_collection.create_index([('user_id', 1), ('date', -1)])
            meals_collection.create_index([('user_id', 1), ('date', -1)])
            goals_collection.create_index([('user_id', 1), ('status', 1)])
        except Exception as idx_error:
            print(f"Index creation note: {idx_error}")
        
        MONGODB_CONNECTED = True
        print("✓ MongoDB connected successfully!")
        return True
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"⚠ MongoDB connection failed: {e}")
        print("Running in frontend-only mode. Database features will be disabled.")
        MONGODB_CONNECTED = False
        return False
    except Exception as e:
        print(f"⚠ MongoDB error: {e}")
        MONGODB_CONNECTED = False
        return False

# Initialize database
if not init_database():
    # Create dummy collections for frontend-only mode
    class DummyCollection:
        def find_one(self, *args, **kwargs): return None
        def find(self, *args, **kwargs): return []
        def insert_one(self, *args, **kwargs): return type('obj', (object,), {'inserted_id': None})()
        def update_one(self, *args, **kwargs): return None
        def sort(self, *args, **kwargs): return self
        def limit(self, *args, **kwargs): return self
        def create_index(self, *args, **kwargs): return None
    
    users_collection = DummyCollection()
    activities_collection = DummyCollection()
    workouts_collection = DummyCollection()
    meals_collection = DummyCollection()
    goals_collection = DummyCollection()
    ai_insights_collection = DummyCollection()
    meal_plans_collection = DummyCollection()

# OpenAI configuration
openai.api_key = config.get('openai-api-key', '')
GROK_API_KEY = config.get('grok-api-key', os.environ.get('GROK_API_KEY', ''))
GEMINI_API_KEY = config.get('gemini-api-key', os.environ.get('GEMINI_API_KEY', ''))

# Utility Functions
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not MONGODB_CONNECTED:
            # In demo mode, allow access
            return f(*args, **kwargs)
        if 'user_id' not in session:
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged-in user"""
    if not MONGODB_CONNECTED or 'user_id' not in session:
        return None
    try:
        user_id = ObjectId(session['user_id'])
        return users_collection.find_one({'_id': user_id})
    except:
        return None

def send_email_otp(receiver_email, otp):
    try:
        smtp_host = os.environ.get('SMTP_HOST', 'smtp-relay.brevo.com')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_login = os.environ.get('SMTP_LOGIN', '')
        sender_email = os.environ.get('SMTP_FROM', smtp_login)
        password = os.environ.get('SMTP_KEY', '')
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_login, password)

        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = 'UpTrack - Verification Code'
        body = f'''
        Welcome to UpTrack!
        
        Your verification code is: {otp}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        '''
        message.attach(MIMEText(body, 'plain'))
        
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False

def calculate_bmr_tdee(user_data):
    """Calculate BMR and TDEE using Mifflin-St Jeor Equation"""
    age = user_data.get('age', 30)
    weight = user_data.get('weight', 70)
    height = user_data.get('height', 170)
    gender = user_data.get('gender', 'male')
    activity_level = user_data.get('activity_level', 'sedentary')
    
    # Mifflin-St Jeor Equation (more accurate than Harris-Benedict)
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extra_active': 1.9
    }
    
    tdee = bmr * activity_multipliers.get(activity_level, 1.2)
    return {'bmr': round(bmr, 2), 'tdee': round(tdee, 2)}

def generate_ai_workout_recommendation(user_data, preferences):
    """Generate AI-powered workout recommendations"""
    if not openai.api_key:
        return generate_basic_workout_recommendation(user_data, preferences)
    
    try:
        prompt = f"""
        Generate a personalized workout plan for a {user_data.get('age', 30)}-year-old {user_data.get('gender', 'person')} 
        who is {user_data.get('activity_level', 'moderately_active')} and wants to {preferences.get('goal', 'maintain fitness')}.
        
        Current weight: {user_data.get('weight', 70)} kg
        Height: {user_data.get('height', 170)} cm
        Fitness goal: {preferences.get('goal', 'general fitness')}
        Available time: {preferences.get('time', '30')} minutes per session
        Equipment: {preferences.get('equipment', 'bodyweight')}
        
        Provide a structured workout plan with:
        1. Warm-up exercises (5 minutes)
        2. Main workout exercises with sets and reps
        3. Cool-down exercises (5 minutes)
        4. Rest days recommendation
        
        Format as a clear, actionable plan.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional fitness trainer and nutritionist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {str(e)}")
        return generate_basic_workout_recommendation(user_data, preferences)

def generate_basic_workout_recommendation(user_data, preferences):
    """Fallback basic workout recommendation"""
    goal = preferences.get('goal', 'general fitness')
    time = int(preferences.get('time', 30))
    
    workouts = {
        'weight_loss': f"""
        Warm-up (5 min): Light jogging, arm circles, leg swings
        Main Workout ({time-10} min):
        - Jumping jacks: 3 sets x 20 reps
        - Push-ups: 3 sets x 10-15 reps
        - Squats: 3 sets x 15 reps
        - Plank: 3 sets x 30 seconds
        - Burpees: 3 sets x 10 reps
        Cool-down (5 min): Stretching exercises
        """,
        'muscle_gain': f"""
        Warm-up (5 min): Dynamic stretching
        Main Workout ({time-10} min):
        - Push-ups: 4 sets x 12-15 reps
        - Squats: 4 sets x 15 reps
        - Lunges: 3 sets x 12 each leg
        - Plank: 3 sets x 45 seconds
        - Mountain climbers: 3 sets x 20 reps
        Cool-down (5 min): Static stretching
        """,
        'general_fitness': f"""
        Warm-up (5 min): Light cardio
        Main Workout ({time-10} min):
        - Full body circuit: 3 rounds
        - Jumping jacks: 30 seconds
        - Push-ups: 30 seconds
        - Squats: 30 seconds
        - Rest: 30 seconds
        Cool-down (5 min): Stretching
        """
    }
    
    return workouts.get(goal, workouts['general_fitness'])

def generate_ai_meal_plan(user_data, preferences):
    """Generate AI-powered meal plan"""
    if not openai.api_key:
        return generate_basic_meal_plan(user_data, preferences)
    
    try:
        tdee_data = calculate_bmr_tdee(user_data)
        tdee = tdee_data['tdee']
        
        prompt = f"""
        Create a personalized meal plan for a {user_data.get('age', 30)}-year-old {user_data.get('gender', 'person')}
        with a TDEE of {tdee} calories.
        
        Dietary preferences: {', '.join(user_data.get('dietary_preferences', ['none']))}
        Health conditions: {', '.join(user_data.get('health_conditions', ['none']))}
        Goal: {preferences.get('goal', 'maintain weight')}
        Meals per day: {preferences.get('meals', 3)}
        
        Provide a daily meal plan with:
        1. Breakfast with calories
        2. Lunch with calories
        3. Dinner with calories
        4. Optional snacks
        5. Total daily calories
        
        Make it practical and easy to follow.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a professional nutritionist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {str(e)}")
        return generate_basic_meal_plan(user_data, preferences)

def generate_basic_meal_plan(user_data, preferences):
    """Fallback basic meal plan"""
    tdee_data = calculate_bmr_tdee(user_data)
    tdee = tdee_data['tdee']
    
    return f"""
    Daily Meal Plan (Target: {tdee:.0f} calories)
    
    Breakfast (~{int(tdee*0.25)} calories):
    - Oatmeal with fruits and nuts
    - Or eggs with whole grain toast
    
    Lunch (~{int(tdee*0.35)} calories):
    - Grilled chicken/fish with vegetables and quinoa
    - Or vegetarian bowl with legumes
    
    Dinner (~{int(tdee*0.30)} calories):
    - Lean protein with steamed vegetables
    - Or plant-based protein with salad
    
    Snacks (~{int(tdee*0.10)} calories):
    - Greek yogurt, fruits, or nuts
    """

def generate_ai_health_insights(user_data, recent_data):
    """Generate AI-powered health insights"""
    if not openai.api_key:
        return generate_basic_insights(user_data, recent_data)
    
    try:
        prompt = f"""
        Analyze this user's health data and provide personalized insights:
        
        User Profile:
        - Age: {user_data.get('age', 30)}
        - Weight: {user_data.get('weight', 70)} kg
        - Height: {user_data.get('height', 170)} cm
        - Activity Level: {user_data.get('activity_level', 'moderately_active')}
        - Goals: {user_data.get('fitness_goals', ['general fitness'])}
        
        Recent Activity:
        - Activities logged: {len(recent_data.get('activities', []))}
        - Workouts completed: {len(recent_data.get('workouts', []))}
        - Meals logged: {len(recent_data.get('meals', []))}
        
        Provide 3-5 actionable insights and recommendations to improve their health and fitness journey.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a health and wellness expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI error: {str(e)}")
        return generate_basic_insights(user_data, recent_data)

def generate_basic_insights(user_data, recent_data):
    """Fallback basic insights"""
    insights = []
    
    if len(recent_data.get('activities', [])) < 3:
        insights.append("Try to log at least 3 activities per week to track your progress better.")
    
    if len(recent_data.get('workouts', [])) < 2:
        insights.append("Consider adding more workout sessions to achieve your fitness goals faster.")
    
    if user_data.get('activity_level') == 'sedentary':
        insights.append("Increasing your daily activity level can significantly improve your overall health.")
    
    return "\n".join(insights) if insights else "Keep up the great work! Continue tracking your activities regularly."

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not MONGODB_CONNECTED:
        if request.method == 'POST':
            flash('MongoDB not connected. You can view the signup form but cannot create accounts. This is a demo mode.', 'error')
        return render_template('signup.html')
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'email', 'phone', 'password', 'dob', 'gender', 'weight', 'height', 'activity_level']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.replace("_", " ").title()} is required.', 'error')
                    return render_template('signup.html')
            
            # Check if email already exists
            if users_collection.find_one({'email': request.form['email']}):
                flash('Email already registered. Please login.', 'error')
                return redirect(url_for('login'))
            
            # Hash password
            hashed_password = hash_password(request.form['password'])
            
            # Calculate age
            dob = datetime.datetime.strptime(request.form['dob'], '%Y-%m-%d')
            age = (datetime.datetime.now() - dob).days // 365
            
            user_data = {
                'name': request.form['name'],
                'email': request.form['email'],
                'phone': request.form['phone'],
                'password': hashed_password,  # Store hashed password
                'dob': request.form['dob'],
                'age': age,
                'gender': request.form['gender'],
                'weight': float(request.form['weight']),
                'height': float(request.form['height']),
                'activity_level': request.form['activity_level'],
                'dietary_preferences': request.form.getlist('dietary_preferences'),
                'health_conditions': request.form.getlist('health_conditions'),
                'fitness_goals': request.form.getlist('fitness_goals'),
                'verified': False,
                'created_at': datetime.datetime.now(),
                'last_login': None
            }
            
            # Generate OTP
            otp = generate_otp()
            user_data['otp'] = otp
            user_data['otp_expires'] = datetime.datetime.now() + datetime.timedelta(minutes=10)
            
            # Insert user
            result = users_collection.insert_one(user_data)
            
            # Send OTP
            if send_email_otp(user_data['email'], otp):
                flash('Verification code sent to your email!', 'success')
                session['temp_user_id'] = str(result.inserted_id)
                session.permanent = True
                return redirect(url_for('verify'))
            else:
                flash('Failed to send verification email. Please try again.', 'error')
                
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
    
    return render_template('signup.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if not MONGODB_CONNECTED:
        flash('MongoDB not connected. This is a demo mode.', 'error')
        return render_template('verify.html')
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        user_id = session.get('temp_user_id')
        
        if not otp or not user_id:
            flash('Invalid verification code.', 'error')
            return render_template('verify.html')
        
        try:
            user = users_collection.find_one({'_id': ObjectId(user_id), 'otp': otp})

            if user:
                # Check if OTP expired
                if user.get('otp_expires') and user['otp_expires'] < datetime.datetime.now():
                    flash('Verification code has expired. Please sign up again.', 'error')
                    session.pop('temp_user_id', None)
                    return redirect(url_for('signup'))
                
                # Verify user
                users_collection.update_one(
                    {'_id': ObjectId(user_id)},
                    {
                        '$set': {'verified': True, 'verified_at': datetime.datetime.now()},
                        '$unset': {'otp': '', 'otp_expires': ''}
                    }
                )
                
                session.pop('temp_user_id', None)
                session['user_id'] = str(user['_id'])
                session.permanent = True
                flash('Account verified successfully! Welcome to UpTrack!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid verification code. Please try again.', 'error')
        except Exception as e:
            flash('An error occurred during verification.', 'error')
    
    return render_template('verify.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session and MONGODB_CONNECTED:
        # Check if user still exists
        user = get_current_user()
        if user:
            return redirect(url_for('dashboard'))
        else:
            session.pop('user_id', None)
    
    # Frontend-only mode: allow viewing pages without login
    if not MONGODB_CONNECTED:
        if request.method == 'POST':
            flash('MongoDB not connected. You can view pages but cannot login. This is a demo mode.', 'error')
        return render_template('login.html')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        user = users_collection.find_one({'email': email})
        
        if user:
            # Check password (support both hashed and plain for migration)
            password_valid = False
            if user.get('password'):
                if user['password'].startswith('$2b$'):  # bcrypt hash
                    password_valid = check_password(password, user['password'])
                else:
                    # Legacy plain password - upgrade to hash
                    if user['password'] == password:
                        password_valid = True
                        # Upgrade to hashed password
                        users_collection.update_one(
                            {'_id': user['_id']},
                            {'$set': {'password': hash_password(password)}}
                        )
            
            if password_valid:
                if user.get('verified', False):
                    session['user_id'] = str(user['_id'])
                    session.permanent = True
                    
                    # Update last login
                    users_collection.update_one(
                        {'_id': user['_id']},
                        {'$set': {'last_login': datetime.datetime.now()}}
                    )
                    
                    flash('Login successful! Welcome back!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    # Resend a fresh OTP
                    new_otp = generate_otp()
                    users_collection.update_one(
                        {'_id': user['_id']},
                        {'$set': {'otp': new_otp, 'otp_expires': datetime.datetime.now() + datetime.timedelta(minutes=10)}}
                    )
                    send_email_otp(user['email'], new_otp)
                    session['temp_user_id'] = str(user['_id'])
                    flash('A new verification code has been sent to your email.', 'success')
                    return redirect(url_for('verify'))
            else:
                flash('Invalid email or password.', 'error')
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Frontend-only mode: show demo dashboard
    if not MONGODB_CONNECTED:
        demo_user = {
            'name': 'Demo User',
            'weight': 70,
            'height': 175,
            'age': 30,
            'gender': 'male',
            'activity_level': 'moderately_active'
        }
        demo_tdee = calculate_bmr_tdee(demo_user)
        demo_insights = "This is a demo view. Connect MongoDB to see your actual data and use all features."
        
        return render_template('dashboard.html', 
                             user=demo_user, 
                             activities=[],
                             workouts=[],
                             meals=[],
                             goals=[],
                             tdee_data=demo_tdee,
                             ai_insights=demo_insights)
    
    user = get_current_user()
    if not user:
        session.pop('user_id', None)
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    
    # Get recent data with proper error handling
    try:
        recent_activities = list(activities_collection.find({'user_id': user_id}).sort('date', -1).limit(5))
        recent_workouts = list(workouts_collection.find({'user_id': user_id}).sort('date', -1).limit(5))
        recent_meals = list(meals_collection.find({'user_id': user_id}).sort('date', -1).limit(5))
        active_goals = list(goals_collection.find({'user_id': user_id, 'status': 'active'}))
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        recent_activities = []
        recent_workouts = []
        recent_meals = []
        active_goals = []
    
    # Calculate stats
    tdee_data = calculate_bmr_tdee(user)
    
    # Get AI insights
    recent_data = {
        'activities': recent_activities,
        'workouts': recent_workouts,
        'meals': recent_meals
    }
    ai_insights = generate_ai_health_insights(user, recent_data)
    
    return render_template('dashboard.html', 
                         user=user, 
                         activities=recent_activities,
                         workouts=recent_workouts,
                         meals=recent_meals,
                         goals=active_goals,
                         tdee_data=tdee_data,
                         ai_insights=ai_insights)

@app.route('/activities', methods=['GET', 'POST'])
def activities():
    if not MONGODB_CONNECTED:
        # Frontend-only mode
        if request.method == 'POST':
            flash('MongoDB not connected. This is a demo view only.', 'error')
            return redirect(url_for('activities'))
        return render_template('activities.html', activities=[])
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    
    if request.method == 'POST':
        activity_data = {
            'user_id': user_id,
            'date': datetime.datetime.strptime(request.form['date'], '%Y-%m-%d'),
            'steps': int(request.form.get('steps', 0) or 0),
            'distance': float(request.form.get('distance', 0) or 0),
            'calories_burned': float(request.form.get('calories_burned', 0) or 0),
            'active_minutes': int(request.form.get('active_minutes', 0) or 0),
            'sleep_hours': float(request.form.get('sleep_hours', 0) or 0),
            'water_intake': float(request.form.get('water_intake', 0) or 0),
            'activity_type': request.form.get('activity_type', 'walking'),
            'notes': request.form.get('notes', '')
        }
        activities_collection.insert_one(activity_data)
        flash('Activity logged successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    user_activities = list(activities_collection.find({'user_id': user_id}).sort('date', -1))
    return render_template('activities.html', activities=user_activities)

@app.route('/workouts', methods=['GET', 'POST'])
def workouts():
    if not MONGODB_CONNECTED:
        # Frontend-only mode
        demo_user = {'name': 'Demo User'}
        if request.method == 'POST':
            flash('MongoDB not connected. This is a demo view only.', 'error')
            return redirect(url_for('workouts'))
        return render_template('workouts.html', workouts=[], user=demo_user)
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    user = users_collection.find_one({'_id': user_id})
    
    if request.method == 'POST':
        workout_data = {
            'user_id': user_id,
            'date': datetime.datetime.strptime(request.form['date'], '%Y-%m-%d'),
            'workout_type': request.form['workout_type'],
            'duration': int(request.form.get('duration', 0)),
            'calories_burned': float(request.form.get('calories_burned', 0)),
            'exercises': request.form.get('exercises', ''),
            'notes': request.form.get('notes', '')
        }
        workouts_collection.insert_one(workout_data)
        flash('Workout logged successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    user_workouts = list(workouts_collection.find({'user_id': user_id}).sort('date', -1))
    return render_template('workouts.html', workouts=user_workouts, user=user)

@app.route('/ai-workout-generator', methods=['GET', 'POST'])
def ai_workout_generator():
    # Demo user for frontend viewing
    demo_user = {
        'age': 30,
        'gender': 'male',
        'weight': 70,
        'height': 175,
        'activity_level': 'moderately_active'
    }
    
    if not MONGODB_CONNECTED:
        user = demo_user
    elif 'user_id' not in session:
        user = demo_user
    else:
        user_id = ObjectId(session['user_id'])
        user = users_collection.find_one({'_id': user_id}) or demo_user
    
    workout_plan = None
    
    if request.method == 'POST':
        preferences = {
            'goal': request.form.get('goal', 'general_fitness'),
            'time': request.form.get('time', '30'),
            'equipment': request.form.get('equipment', 'bodyweight')
        }
        
        workout_plan = generate_ai_workout_recommendation(user, preferences)
        
        # Save to database only if connected
        if MONGODB_CONNECTED and 'user_id' in session:
            workout_data = {
                'user_id': ObjectId(session['user_id']),
                'date': datetime.datetime.now(),
                'workout_type': 'AI Generated',
                'plan': workout_plan,
                'preferences': preferences
            }
            workouts_collection.insert_one(workout_data)
    
    return render_template('ai_workout_generator.html', user=user, workout_plan=workout_plan)

@app.route('/meals', methods=['GET', 'POST'])
def meals():
    if not MONGODB_CONNECTED:
        # Frontend-only mode
        if request.method == 'POST':
            flash('MongoDB not connected. This is a demo view only.', 'error')
            return redirect(url_for('meals'))
        return render_template('meals.html', meals=[])
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    
    if request.method == 'POST':
        meal_data = {
            'user_id': user_id,
            'date': datetime.datetime.strptime(request.form['date'], '%Y-%m-%d'),
            'meal_type': request.form['meal_type'],
            'food_items': request.form['food_items'],
            'calories': float(request.form.get('calories', 0)),
            'protein': float(request.form.get('protein', 0)),
            'carbs': float(request.form.get('carbs', 0)),
            'fats': float(request.form.get('fats', 0)),
            'notes': request.form.get('notes', '')
        }
        meals_collection.insert_one(meal_data)
        flash('Meal logged successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    user_meals = list(meals_collection.find({'user_id': user_id}).sort('date', -1))
    return render_template('meals.html', meals=user_meals)

@app.route('/ai-meal-planner', methods=['GET', 'POST'])
def ai_meal_planner():
    # Demo user for frontend viewing
    demo_user = {
        'age': 30,
        'gender': 'male',
        'weight': 70,
        'height': 175,
        'activity_level': 'moderately_active',
        'dietary_preferences': [],
        'health_conditions': []
    }
    
    if not MONGODB_CONNECTED:
        user = demo_user
    elif 'user_id' not in session:
        user = demo_user
    else:
        user_id = ObjectId(session['user_id'])
        user = users_collection.find_one({'_id': user_id}) or demo_user
    
    meal_plan = None
    
    if request.method == 'POST':
        preferences = {
            'goal': request.form.get('goal', 'maintain_weight'),
            'meals': request.form.get('meals', '3')
        }
        
        meal_plan = generate_ai_meal_plan(user, preferences)
        
        # Save to database only if connected
        if MONGODB_CONNECTED and 'user_id' in session:
            plan_data = {
                'user_id': ObjectId(session['user_id']),
                'date': datetime.datetime.now(),
                'plan': meal_plan,
                'preferences': preferences
            }
            meal_plans_collection.insert_one(plan_data)
    
    tdee_data = calculate_bmr_tdee(user)
    return render_template('ai_meal_planner.html', user=user, meal_plan=meal_plan, tdee_data=tdee_data)

@app.route('/goals', methods=['GET', 'POST'])
def goals():
    if not MONGODB_CONNECTED:
        # Frontend-only mode
        if request.method == 'POST':
            flash('MongoDB not connected. This is a demo view only.', 'error')
            return redirect(url_for('goals'))
        return render_template('goals.html', goals=[])
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    
    if request.method == 'POST':
        goal_data = {
            'user_id': user_id,
            'goal_type': request.form['goal_type'],
            'target': request.form['target'],
            'deadline': datetime.datetime.strptime(request.form['deadline'], '%Y-%m-%d'),
            'description': request.form.get('description', ''),
            'status': 'active',
            'created_at': datetime.datetime.now()
        }
        goals_collection.insert_one(goal_data)
        flash('Goal set successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    user_goals = list(goals_collection.find({'user_id': user_id}).sort('created_at', -1))
    return render_template('goals.html', goals=user_goals)

@app.route('/progress')
def progress():
    # Demo data for frontend viewing
    demo_dates = ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
    demo_steps = [5000, 6000, 7000, 6500, 8000]
    demo_calories = [200, 250, 300, 280, 350]
    demo_duration = [30, 45, 30, 60, 45]
    demo_meal_calories = [1800, 2000, 1900, 2100, 1950]
    
    if not MONGODB_CONNECTED or 'user_id' not in session:
        return render_template('progress.html',
                             activity_dates=json.dumps(demo_dates),
                             steps_data=json.dumps(demo_steps),
                             calories_data=json.dumps(demo_calories),
                             workout_dates=json.dumps(demo_dates),
                             workout_duration=json.dumps(demo_duration),
                             meal_dates=json.dumps(demo_dates),
                             meal_calories=json.dumps(demo_meal_calories))
    
    user_id = ObjectId(session['user_id'])
    
    # Get data for charts
    activities = list(activities_collection.find({'user_id': user_id}).sort('date', 1))
    workouts = list(workouts_collection.find({'user_id': user_id}).sort('date', 1))
    meals = list(meals_collection.find({'user_id': user_id}).sort('date', 1))
    
    # Prepare chart data
    activity_dates = [a['date'].strftime('%Y-%m-%d') for a in activities] if activities else demo_dates
    steps_data = [a.get('steps', 0) for a in activities] if activities else demo_steps
    calories_data = [a.get('calories_burned', 0) for a in activities] if activities else demo_calories
    
    workout_dates = [w['date'].strftime('%Y-%m-%d') for w in workouts] if workouts else demo_dates
    workout_duration = [w.get('duration', 0) for w in workouts] if workouts else demo_duration
    
    meal_dates = [m['date'].strftime('%Y-%m-%d') for m in meals] if meals else demo_dates
    meal_calories = [m.get('calories', 0) for m in meals] if meals else demo_meal_calories
    
    return render_template('progress.html',
                         activity_dates=json.dumps(activity_dates),
                         steps_data=json.dumps(steps_data),
                         calories_data=json.dumps(calories_data),
                         workout_dates=json.dumps(workout_dates),
                         workout_duration=json.dumps(workout_duration),
                         meal_dates=json.dumps(meal_dates),
                         meal_calories=json.dumps(meal_calories))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Demo user for frontend viewing
    demo_user = {
        'name': 'Demo User',
        'phone': '+1234567890',
        'weight': 70,
        'height': 175,
        'activity_level': 'moderately_active',
        'dietary_preferences': ['vegetarian'],
        'health_conditions': [],
        'fitness_goals': ['general_fitness']
    }
    
    if not MONGODB_CONNECTED:
        if request.method == 'POST':
            flash('MongoDB not connected. This is a demo view only.', 'error')
            return redirect(url_for('profile'))
        return render_template('profile.html', user=demo_user)
    
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = ObjectId(session['user_id'])
    user = users_collection.find_one({'_id': user_id})
    
    if not user:
        return render_template('profile.html', user=demo_user)
    
    if request.method == 'POST':
        update_data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'weight': float(request.form['weight']),
            'height': float(request.form['height']),
            'activity_level': request.form['activity_level'],
            'dietary_preferences': request.form.getlist('dietary_preferences'),
            'health_conditions': request.form.getlist('health_conditions'),
            'fitness_goals': request.form.getlist('fitness_goals')
        }
        users_collection.update_one({'_id': user_id}, {'$set': update_data})
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('profile.html', user=user)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if not MONGODB_CONNECTED:
        flash('MongoDB not connected. This feature requires database connection.', 'error')
        return render_template('forgot_password.html')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot_password.html')
        
        user = users_collection.find_one({'email': email})
        
        if user:
            otp = generate_otp()
            otp_expires = datetime.datetime.now() + datetime.timedelta(minutes=10)
            
            users_collection.update_one(
                {'_id': user['_id']},
                {'$set': {'otp': otp, 'otp_expires': otp_expires}}
            )
            
            if send_email_otp(email, otp):
                session['reset_email'] = email
                session.permanent = True
                flash('Password reset code sent to your email!', 'success')
                return redirect(url_for('reset_password'))
            else:
                flash('Failed to send email. Please check your email configuration.', 'error')
        else:
            # Don't reveal if email exists for security
            flash('If that email exists, a reset code has been sent.', 'success')
            return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not MONGODB_CONNECTED:
        flash('MongoDB not connected. This feature requires database connection.', 'error')
        return redirect(url_for('forgot_password'))
    
    if 'reset_email' not in session:
        flash('Please request a password reset first.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not otp or not new_password or not confirm_password:
            flash('All fields are required.', 'error')
            return render_template('reset_password.html')
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html')
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('reset_password.html')
        
        try:
            user = users_collection.find_one({'email': session['reset_email'], 'otp': otp})
            if user:
                # Check if OTP expired
                if user.get('otp_expires') and user['otp_expires'] < datetime.datetime.now():
                    flash('Verification code has expired. Please request a new one.', 'error')
                    session.pop('reset_email', None)
                    return redirect(url_for('forgot_password'))
                
                # Hash and update password
                hashed_password = hash_password(new_password)
                users_collection.update_one(
                    {'_id': user['_id']},
                    {
                        '$set': {'password': hashed_password, 'password_reset_at': datetime.datetime.now()},
                        '$unset': {'otp': '', 'otp_expires': ''}
                    }
                )
                session.pop('reset_email', None)
                flash('Password reset successfully! Please login with your new password.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Invalid verification code.', 'error')
        except Exception as e:
            flash('An error occurred. Please try again.', 'error')
    return render_template('reset_password.html')

@app.route('/posture')
def posture():
    return render_template('posture.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'reply': "I didn't catch that. Could you repeat?"}), 400
            
        system_prompt = "You are a friendly, encouraging, and knowledgeable AI wellness coach. Provide concise, helpful advice regarding fitness, mental health, diet, and general wellbeing. Use formatting like bullet points when appropriate."
            
        # Try Grok API first if configured
        if GROK_API_KEY:
            try:
                client = openai.OpenAI(
                    api_key=GROK_API_KEY,
                    base_url="https://api.x.ai/v1",
                )
                
                completion = client.chat.completions.create(
                    model="grok-3",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                )
                
                reply = completion.choices[0].message.content
                return jsonify({'reply': reply})
            except Exception as e:
                print(f"Grok API Error, falling back: {e}")
                pass # Fall through to Gemini
                
        # Fallback to Gemini API
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY) # Configure genai with API key
                
                # Prepend the system prompt to the user's message since some older gemini setups handle system prompts differently
                # For newer Gemini models, system instructions can be passed directly.
                # For 'gemini-2.5-flash', it's often better to integrate system instructions into the first user message.
                combined_prompt = f"System Instructions: {system_prompt}\n\nUser Question: {user_message}"
                
                model = genai.GenerativeModel('gemini-flash-latest')
                response = model.generate_content(combined_prompt)
                
                return jsonify({'reply': response.text})
            except Exception as e:
                print(f"Gemini API Error: {e}")
                return jsonify({'reply': "Sorry, my Gemini AI brain is having trouble too. Please try again later.", "error": str(e)}), 500
        
        return jsonify({'reply': "Sorry, no AI brain (Grok or Gemini) is configured yet! Please set GEMINI_API_KEY or GROK_API_KEY.", "error": "No API Keys found."})
        
    except Exception as e:
        print(f"Chat API System Error: {e}")
        return jsonify({'reply': "Sorry, I hit an unexpected error while processing your request. Please try again.", "error": str(e)}), 500

@app.route('/api/analyze-photo', methods=['POST'])
def analyze_photo():
    try:
        data = request.json
        image_data = data.get('image', '')

        if not image_data:
            return jsonify({'error': 'No image provided.'}), 400

        # Clean the base64 string if it contains the data uri prefix
        raw_b64 = image_data.split(',')[1] if ',' in image_data else image_data
        prompt_text = "Analyze this workout form. Provide a brief 2-3 sentence feedback on their posture, form, and any noticeable areas of improvement or safety tips."

        # Try Grok Vision first
        if GROK_API_KEY:
            try:
                client = openai.OpenAI(api_key=GROK_API_KEY, base_url="https://api.x.ai/v1")
                response = client.chat.completions.create(
                    model="grok-2-vision-latest",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{raw_b64}", "detail": "high"}}
                        ]
                    }],
                    max_tokens=300
                )
                return jsonify({'analysis': response.choices[0].message.content})
            except Exception as e:
                print(f"Grok Vision Error, falling back to Gemini: {e}")

        # Fallback to Gemini Vision
        if GEMINI_API_KEY:
            try:
                import PIL.Image
                import io
                import base64
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-flash-latest')
                img_bytes = base64.b64decode(raw_b64)
                img = PIL.Image.open(io.BytesIO(img_bytes))
                response = model.generate_content([prompt_text, img])
                return jsonify({'analysis': response.text})
            except Exception as e:
                print(f"Gemini Vision Error: {e}")
                return jsonify({'error': f'Image analysis failed: {str(e)}'}), 500

        return jsonify({'error': 'No vision API key configured.'}), 500

    except Exception as e:
        print(f"Vision API Error: {e}")
        return jsonify({'error': "Failed to analyze photo due to an internal error."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)
