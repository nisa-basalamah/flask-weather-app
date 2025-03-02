from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import requests, random, pytz

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models, routes, etc. will go here
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=0)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer_1 = db.Column(db.String(100), nullable=False)
    answer_2 = db.Column(db.String(100), nullable=False)
    answer_3 = db.Column(db.String(100), nullable=False)
    answer_4 = db.Column(db.String(100), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)

def insert_dummy_data():
    # Delete existing data
    # db.session.query(User).delete()
    # db.session.query(Question).delete()
    # db.session.commit()  # Commit deletion before inserting new data

    # print("Existing data deleted. Inserting fresh dummy data...")

    # Check if data already exists
    if User.query.first() or Question.query.first():
        print("Dummy data already exists. Skipping insertion.")
        return

    # Insert dummy users
    dummy_users = [
        User(username="user1", password="user1", nickname="user1", score=50),
        User(username="user2", password="user2", nickname="user2", score=30),
        User(username="user3", password="user3", nickname="user3", score=70),
        User(username="user4", password="user4", nickname="user4", score=20),
        User(username="user5", password="user5", nickname="user5", score=40),
    ]

    # Insert dummy questions
    dummy_questions = [
        Question(question="What does AI stand for?", answer_1="Artificial Intelligence", answer_2="Automated Information",
                 answer_3="Applied Infrastructure", answer_4="Augmented Innovation", correct_answer="Artificial Intelligence"),
        Question(question="Which programming language is widely used for AI?", answer_1="Java", answer_2="C++",
                 answer_3="Python", answer_4="Ruby", correct_answer="Python"),
        Question(question="What is the purpose of NLP in AI?", answer_1="Processing images", answer_2="Understanding human language",
                 answer_3="Managing databases", answer_4="Encrypting data", correct_answer="Understanding human language"),
        Question(question="Which AI field focuses on visual data processing?", answer_1="Robotics", answer_2="Machine Learning",
                 answer_3="Computer Vision", answer_4="Big Data", correct_answer="Computer Vision"),
    ]

    # Add to session and commit
    db.session.add_all(dummy_users)
    db.session.add_all(dummy_questions)
    db.session.commit()

    print("Dummy data inserted successfully!")

# Create Database Tables (Run only once)
# with app.app_context():
    # db.create_all()
    # insert_dummy_data()

API_KEY = "646fe6d36a9399a0d9f2944ebfaab578"
BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Set your local timezone (change to match your location)
local_tz = pytz.timezone("Asia/Jakarta")

@app.route('/', methods=['GET', 'POST'])
def home():
    weather_data = None

    if request.method == "POST":
        city = request.form.get("city")
        if city:
            params = {"q": city, "appid": API_KEY, "units": "metric"}
            response = requests.get(BASE_URL, params=params)
            data = response.json()

            if data.get("list"):
                daily_forecast = {}

                for entry in data["list"]:
                    date = entry["dt_txt"].split(" ")[0]  # Extract date (YYYY-MM-DD)
                    time = entry["dt_txt"].split(" ")[1]  # Extract time (HH:MM:SS)

                    if date not in daily_forecast:
                        daily_forecast[date] = {
                            "day_temp": None,
                            "night_temp": None,
                            "day_weather": None,
                            "night_weather": None,
                            "day_time_diff": float("inf"),  # Track closest time difference
                            "night_time_diff": float("inf"),
                        }

                    # Convert current time to an hour-based integer
                    hour = int(time[:2])  # Extract the hour (e.g., "12" from "12:00:00")

                    # Find the closest available daytime temperature (preferably around 12:00)
                    target_daytime = 12  # Noon is ideal
                    day_diff = abs(hour - target_daytime)

                    if day_diff < daily_forecast[date]["day_time_diff"]:  
                        daily_forecast[date]["day_temp"] = entry["main"]["temp"]
                        daily_forecast[date]["day_weather"] = entry["weather"][0]["description"]
                        daily_forecast[date]["day_time_diff"] = day_diff  

                    # Find the closest available nighttime temperature (preferably around 00:00)
                    target_nighttime = 0  # Midnight is ideal
                    night_diff = abs(hour - target_nighttime)

                    if night_diff < daily_forecast[date]["night_time_diff"]:  
                        daily_forecast[date]["night_temp"] = entry["main"]["temp"]
                        daily_forecast[date]["night_weather"] = entry["weather"][0]["description"]
                        daily_forecast[date]["night_time_diff"] = night_diff  

                # ✅ Get current date based on local timezone
                utc_now = datetime.now(timezone.utc).replace(tzinfo=pytz.utc)
                local_now = utc_now.astimezone(local_tz)
                today = local_now.date()  # Corrected to local date
                
                # Convert to a list and keep only the first 3 days (today, tomorrow, day after)
                three_days_forecast = []
                for i in range(3):
                    target_date = today + timedelta(days=i)
                    formatted_date = target_date.strftime("%A, %d %B %Y")  # Example: Monday, 04 March 2025

                    if str(target_date) in daily_forecast:
                        three_days_forecast.append({
                            "date": formatted_date,
                            "day_temp": daily_forecast[str(target_date)]["day_temp"],
                            "day_weather": daily_forecast[str(target_date)]["day_weather"],
                            "night_temp": daily_forecast[str(target_date)]["night_temp"],
                            "night_weather": daily_forecast[str(target_date)]["night_weather"]
                        })

                weather_data = {"city": city, "forecast": three_days_forecast}

    return render_template("index.html", weather_data=weather_data)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        nickname = request.form['nickname']

        # Check if username or nickname is already taken
        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "error")
            return redirect(url_for('register'))
        if User.query.filter_by(nickname=nickname).first():
            flash("Nickname already exists!", "error")
            return redirect(url_for('register'))
        
        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('register'))

        # Create new user and add to database
        new_user = User(username=username, password=password, nickname=nickname)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('home'))
        
        flash("Invalid credentials!", "error")
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        # Retrieve the question from session
        question_id = session.get('current_question_id')
        question = Question.query.get(question_id)

        if not question:
            flash("Something went wrong. Try again.", "error")
            return redirect(url_for('quiz'))

        selected_answer = request.form['answer']
        if selected_answer == question.correct_answer:
            user.score += 10  # Increase score for correct answer
            db.session.commit()
            flash("Correct! +10 points", "success")
        else:
            flash(f"Incorrect. The correct answer was: {question.correct_answer}", "error")

        # Clear stored question and refresh with a new one
        session.pop('current_question_id', None)
        return redirect(url_for('quiz'))

    # Pick a new random question and store it in session
    questions = Question.query.all()
    if not questions:
        flash("No questions available.", "error")
        return redirect(url_for('home'))

    question = random.choice(questions)
    session['current_question_id'] = question.id  # Store question ID in session

    return render_template('quiz.html', question=question, user=user)

@app.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.score.desc()).all()
    return render_template('leaderboard.html', users=users)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)