from flask import Flask, render_template, request, redirect, session
import sqlite3
import joblib
import pandas as pd

app = Flask(__name__)
app.secret_key = "secretkey123"

# ------------------ Database Setup ------------------
def create_user_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_user_table()

# ------------------ Routes ------------------

@app.route('/')
def home():
    return redirect('/login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists."
        conn.close()
        return redirect('/login')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect('/dashboard')
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        try:
            sleep = int(request.form['SleepQuality'])
            headaches = int(request.form['HeadachesPerWeek'])
            academic = int(request.form['AcademicPerformance'])
            studyload = int(request.form['StudyLoad'])
            extra = int(request.form['ExtracurricularFreq'])

            input_df = pd.DataFrame([{
                "SleepQuality": sleep,
                "HeadachesPerWeek": headaches,
                "AcademicPerformance": academic,
                "StudyLoad": studyload,
                "ExtracurricularFreq": extra
            }])

            model = joblib.load('model/stress_prediction_model.joblib')
            raw_prediction = model.predict(input_df)[0]

            prediction = int(raw_prediction)

            label_map = {
                1: 'Very Low',
                2: 'Low',
                3: 'Moderate',
                4: 'High',
                5: 'Very High'
            }
            stress_level = label_map.get(prediction, 'Unknown')

            if prediction == 5:
                ai_tip = "🔥 Very High Stress: Please take immediate steps like counseling, proper rest, and relaxation."
            elif prediction == 4:
                ai_tip = "🔴 High Stress: Take regular breaks, manage time, and talk to friends or mentors."
            elif prediction == 3:
                ai_tip = "🟠 Moderate Stress: Balance is key. Try to reduce workload and get rest."
            elif prediction == 2:
                ai_tip = "🟡 Low Stress: Doing well! Just keep taking care of your routine."
            elif prediction == 1:
                ai_tip = "🟢 Very Low Stress: Excellent! You are managing everything well."
            else:
                ai_tip = "⚠️ Prediction could not be understood."

            return render_template('result.html',
                                   prediction=stress_level,
                                   ai_tip=ai_tip,
                                   input_data=input_df.iloc[0].to_dict())
        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    return render_template('dashboard.html', user=session['username'])



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
