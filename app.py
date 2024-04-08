from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import threading
import time
from datetime import datetime
import pygame
import json

app = Flask(__name__)

# Ключ для сессий
app.secret_key = 'your_secret_key'

# Папка для загруженных файлов
UPLOAD_FOLDER = 'uploaded_files'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}

# Создание папки для загруженных файлов, если она не существует
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

pygame.mixer.init()

# Жестко закодированные данные пользователя
USERNAME = 'admin'
PASSWORD = 'admin'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

schedule_file = 'schedule.json'

try:
    with open(schedule_file, 'r') as file:
        schedule = json.load(file)
except FileNotFoundError:
    schedule = []

def play_sound(audio_file_path):
    pygame.mixer.music.load(audio_file_path)
    pygame.mixer.music.play()

def check_schedule():
    while True:
        now = datetime.now().strftime('%H:%M')
        for time_slot in schedule:
            if now == time_slot['lesson_start'] or now == time_slot['lesson_end']:
                audio_file_path = time_slot['audio_file_path']
                play_sound(audio_file_path)
                time.sleep(120)
                break
        time.sleep(2)

def save_schedule():
    with open(schedule_file, 'w') as file:
        json.dump(schedule, file)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('schedule_page'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def schedule_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # Здесь код для работы с расписанием
    return render_template('index.html', schedule=schedule)

if __name__ == '__main__':
    threading.Thread(target=check_schedule, daemon=True).start()
    app.run(debug=True)
