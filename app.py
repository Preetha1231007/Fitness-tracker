from flask import Flask, render_template, request, redirect, url_for, session, flash
import pickle
import numpy as np
import os
from datetime import datetime

app = Flask(__name__, static_folder='staticcss', static_url_path='/static')
app.secret_key = 'fitness_tracker_secret_key'

# Simple in-memory storage (in a real app, use a database)
users = {}
meal_logs = {}
workout_logs = {}

# Load ML model (we'll create a simple one for demonstration)
def get_model_path(model_name):
    return os.path.join('models', f'{model_name}.pkl')

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

# Simple ML model for meal recommendations based on user data
def create_meal_model():
    # This is a very simplified model for demonstration
    # In a real app, you would train a proper ML model
    meal_plans = {
        'weight_loss': {
            'breakfast': ['Oatmeal with fruits', 'Greek yogurt with berries', 'Egg white omelet'],
            'lunch': ['Grilled chicken salad', 'Quinoa bowl', 'Tuna sandwich'],
            'dinner': ['Baked salmon with vegetables', 'Turkey and vegetable stir fry', 'Lentil soup']
        },
        'muscle_gain': {
            'breakfast': ['Protein pancakes', 'Eggs and whole grain toast', 'Protein smoothie'],
            'lunch': ['Chicken and rice', 'Beef and sweet potato', 'Tuna pasta'],
            'dinner': ['Salmon and quinoa', 'Steak and vegetables', 'Chicken and pasta']
        },
        'maintenance': {
            'breakfast': ['Avocado toast', 'Fruit smoothie', 'Cereal with milk'],
            'lunch': ['Turkey wrap', 'Vegetable soup', 'Chicken sandwich'],
            'dinner': ['Fish tacos', 'Vegetable stir fry', 'Pasta with tomato sauce']
        }
    }
    
    # Save the simple model
    with open(get_model_path('meal_model'), 'wb') as f:
        pickle.dump(meal_plans, f)

# Simple ML model for workout recommendations
def create_workout_model():
    # This is a very simplified model for demonstration
    workout_plans = {
        'beginner': {
            'cardio': ['Walking 30 minutes', 'Light cycling', 'Swimming'],
            'strength': ['Bodyweight squats', 'Wall push-ups', 'Assisted lunges'],
            'flexibility': ['Basic stretching', 'Beginner yoga', 'Mobility exercises']
        },
        'intermediate': {
            'cardio': ['Jogging 30 minutes', 'Cycling intervals', 'HIIT 15 minutes'],
            'strength': ['Dumbbell exercises', 'Resistance band workouts', 'Circuit training'],
            'flexibility': ['Intermediate yoga', 'Dynamic stretching', 'Pilates']
        },
        'advanced': {
            'cardio': ['Running 45 minutes', 'HIIT 30 minutes', 'Spinning class'],
            'strength': ['Weight training', 'Advanced calisthenics', 'CrossFit'],
            'flexibility': ['Advanced yoga', 'Deep stretching routines', 'Mobility drills']
        }
    }
    
    # Save the simple model
    with open(get_model_path('workout_model'), 'wb') as f:
        pickle.dump(workout_plans, f)

# Create models if they don't exist
if not os.path.exists(get_model_path('meal_model')):
    create_meal_model()
    
if not os.path.exists(get_model_path('workout_model')):
    create_workout_model()

# Load models
try:
    with open(get_model_path('meal_model'), 'rb') as f:
        meal_model = pickle.load(f)
    with open(get_model_path('workout_model'), 'rb') as f:
        workout_model = pickle.load(f)
except:
    # If loading fails, create new models
    create_meal_model()
    create_workout_model()
    with open(get_model_path('meal_model'), 'rb') as f:
        meal_model = pickle.load(f)
    with open(get_model_path('workout_model'), 'rb') as f:
        workout_model = pickle.load(f)

# Calculate BMI and determine fitness goal
def calculate_metrics(weight, height, age, activity_level):
    # Convert height from cm to m
    height_m = height / 100
    
    # Calculate BMI
    bmi = weight / (height_m ** 2)
    
    # Determine fitness goal based on BMI
    if bmi < 18.5:
        goal = 'muscle_gain'
    elif bmi > 25:
        goal = 'weight_loss'
    else:
        goal = 'maintenance'
    
    # Calculate daily calorie needs (simplified)
    # Harris-Benedict equation (simplified)
    if activity_level == 'sedentary':
        activity_factor = 1.2
    elif activity_level == 'lightly_active':
        activity_factor = 1.375
    elif activity_level == 'moderately_active':
        activity_factor = 1.55
    elif activity_level == 'very_active':
        activity_factor = 1.725
    else:
        activity_factor = 1.9  # extremely_active
    
    # Base Metabolic Rate (BMR) calculation
    if session['gender'] == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    # Daily calorie needs
    daily_calories = bmr * activity_factor
    
    # Adjust based on goal
    if goal == 'weight_loss':
        daily_calories -= 500  # Deficit for weight loss
    elif goal == 'muscle_gain':
        daily_calories += 500  # Surplus for muscle gain
    
    # Determine fitness level based on activity
    if activity_level in ['sedentary', 'lightly_active']:
        fitness_level = 'beginner'
    elif activity_level == 'moderately_active':
        fitness_level = 'intermediate'
    else:
        fitness_level = 'advanced'
    
    return {
        'bmi': round(bmi, 2),
        'goal': goal,
        'daily_calories': round(daily_calories),
        'fitness_level': fitness_level
    }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        age = int(request.form['age'])
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        gender = request.form['gender']
        activity_level = request.form['activity_level']
        
        # Store user data
        user_id = len(users) + 1
        users[user_id] = {
            'name': name,
            'age': age,
            'weight': weight,
            'height': height,
            'gender': gender,
            'activity_level': activity_level,
            'registration_date': datetime.now()
        }
        
        # Set session
        session['user_id'] = user_id
        session['name'] = name
        session['age'] = age
        session['weight'] = weight
        session['height'] = height
        session['gender'] = gender
        session['activity_level'] = activity_level
        
        # Calculate metrics
        metrics = calculate_metrics(weight, height, age, activity_level)
        session['bmi'] = metrics['bmi']
        session['goal'] = metrics['goal']
        session['daily_calories'] = metrics['daily_calories']
        session['fitness_level'] = metrics['fitness_level']
        
        flash(f'Welcome {name}! Your account has been created successfully.')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please register or login first.')
        return redirect(url_for('register'))
    
    # Get user data from session
    user_data = {
        'name': session['name'],
        'age': session['age'],
        'weight': session['weight'],
        'height': session['height'],
        'gender': session['gender'],
        'activity_level': session['activity_level'],
        'bmi': session['bmi'],
        'goal': session['goal'],
        'daily_calories': session['daily_calories'],
        'fitness_level': session['fitness_level']
    }
    
    # Get meal recommendations
    meal_recommendations = meal_model[user_data['goal']]
    
    # Get workout recommendations
    workout_recommendations = workout_model[user_data['fitness_level']]
    
    # Get user logs
    user_id = session['user_id']
    user_meal_logs = meal_logs.get(user_id, [])
    user_workout_logs = workout_logs.get(user_id, [])
    
    return render_template(
        'dashboard.html',
        user=user_data,
        meal_recommendations=meal_recommendations,
        workout_recommendations=workout_recommendations,
        meal_logs=user_meal_logs,
        workout_logs=user_workout_logs
    )

@app.route('/log_meal', methods=['POST'])
def log_meal():
    if 'user_id' not in session:
        flash('Please register or login first.')
        return redirect(url_for('register'))
    
    meal_name = request.form['meal_name']
    calories = int(request.form['calories'])
    meal_type = request.form['meal_type']
    
    user_id = session['user_id']
    if user_id not in meal_logs:
        meal_logs[user_id] = []
    
    meal_logs[user_id].append({
        'meal_name': meal_name,
        'calories': calories,
        'meal_type': meal_type,
        'date': datetime.now()
    })
    
    flash('Meal logged successfully!')
    return redirect(url_for('dashboard'))

@app.route('/log_workout', methods=['POST'])
def log_workout():
    if 'user_id' not in session:
        flash('Please register or login first.')
        return redirect(url_for('register'))
    
    workout_name = request.form['workout_name']
    duration = int(request.form['duration'])
    workout_type = request.form['workout_type']
    
    user_id = session['user_id']
    if user_id not in workout_logs:
        workout_logs[user_id] = []
    
    workout_logs[user_id].append({
        'workout_name': workout_name,
        'duration': duration,
        'workout_type': workout_type,
        'date': datetime.now()
    })
    
    flash('Workout logged successfully!')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)