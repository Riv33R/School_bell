from flask import Flask, request, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename
import os
import threading
import time
from datetime import datetime
import pygame
import json

app = Flask(__name__)

UPLOAD_FOLDER = 'uploaded_files'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

pygame.mixer.init()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

schedule_file = 'schedule.json'

try:
    with open(schedule_file, 'r') as file:
        schedule = json.load(file)
except FileNotFoundError:
    schedule = []

# HTML_TEMPLATE обновлен для добавления формы редактирования времени
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Расписание школьных звонков</title>
    <style>
    body, html {
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f4f7f6;
        color: #333;
    }
    .container {
        max-width: 960px;
        margin: 20px auto;
        padding: 20px;
        background-color: #fff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-radius: 8px;
    }
    h1, h2 {
        color: #2c3e50;
        text-align: center;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
    th, td {
        padding: 10px;
        border: 1px solid #ddd;
        text-align: center;
    }
    th {
        background-color: #3498db;
        color: #ffffff;
    }
    td {
        background-color: #ecf0f1;
    }
    .btn, .btn-small {
        display: inline-block;
        padding: 10px 20px;
        font-size: 14px;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
        color: #ffffff;
        background-color: #3498db;
        border: none;
        border-radius: 5px;
        transition: background-color 0.3s ease;
        margin: 5px; /* Универсальный отступ для всех кнопок */
    }
    .btn:hover, .btn-small:hover {
        background-color: #2980b9;
    }
    .btn-danger {
        background-color: #e74c3c;
    }
    .btn-danger:hover {
        background-color: #c0392b;
    }
    form {
        margin-bottom: 20px; /* Добавлен отступ снизу для каждой формы */
    }
    form > * {
        margin: 5px; /* Универсальный отступ для элементов внутри форм */
        display: block; /* Делаем все элементы блочными для лучшего контроля */
    }
    input[type="time"], input[type="file"], button {
        display: inline-block;
        padding: 10px 20px;
        font-size: 14px;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
        \\color: #ffffff;
        \\background-color: #3498db;
        border: none;
        border-radius: 5px;
        transition: background-color 0.3s ease;
        margin: 5px;
    }
    input[type="file"] {
        display: inline-block;
        padding: 10px 20px;
        font-size: 14px;
        cursor: pointer;
        text-align: center;
        text-decoration: none;
        color: #ffffff;
        background-color: #3498db;
        border: none;
        border-radius: 5px;
        transition: background-color 0.3s ease;
        margin: 5px;
    }
</style>

</head>
<body>
    <div class="container">
        <h1>Расписание школьных звонков</h1>
        <div id="clock" style="text-align:center; font-size:24px; margin-bottom: 20px;"></div>
        <table>
            <thead>
                <tr>
                    <th>Начало урока</th>
                    <th>Конец урока</th>
                    <th>Аудио файл</th>
                    <th>Действие</th>
                </tr>
            </thead>
            <tbody>
                {% for time_slot in schedule %}
                <tr>
                    <td>{{ time_slot['lesson_start'] }}</td>
                    <td>{{ time_slot['lesson_end'] }}</td>
                    <td>{{ time_slot.get('audio_file_path', 'Не указан') }}</td>
                    <td>
                        <form method="post" action="/delete/{{ loop.index0 }}">
                            <button type="submit" class="btn btn-small btn-danger">Удалить</button>
                        </form>
                        <form method="post" action="/replace_audio/{{ loop.index0 }}" enctype="multipart/form-data">
                            <input type="file" name="audio_file" accept=".mp3,.wav,.ogg" required>
                            <button type="submit" class="btn btn-small">Заменить аудио</button>
                        </form>
                        <!-- Добавлена форма для редактирования времени -->
                        <form method="post" action="/edit_time/{{ loop.index0 }}">
                            <input type="time" name="lesson_start" value="{{ time_slot['lesson_start'] }}" required>
                            <input type="time" name="lesson_end" value="{{ time_slot['lesson_end'] }}" required>
                            <button type="submit" class="btn btn-small">Редактировать время</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <h2>Добавить время звонка</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="time" name="lesson_start" required> Начало урока
            <input type="time" name="lesson_end" required> Конец урока
            <input type="file" name="audio_file" accept=".mp3,.wav,.ogg" required> Аудио файл
            <button type="submit" class="btn">Добавить и загрузить</button>
        </form>
    </div>
    <script>
        function updateClock() {
            const now = new Date();
            document.getElementById('clock').innerHTML = now.toLocaleTimeString();
        }
        setInterval(updateClock, 1000);
    </script>
</body>
</html>
"""

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

@app.route('/', methods=['GET', 'POST'])
def schedule_page():
    if request.method == 'POST':
        lesson_start = request.form.get('lesson_start')
        lesson_end = request.form.get('lesson_end')
        audio_file = request.files.get('audio_file')
        
        if lesson_start and lesson_end and audio_file and allowed_file(audio_file.filename):
            filename = secure_filename(audio_file.filename)
            audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(audio_file_path)
            
            schedule.append({
                'lesson_start': lesson_start, 
                'lesson_end': lesson_end, 
                'audio_file_path': audio_file_path
            })
            save_schedule()
            
        return redirect(url_for('schedule_page'))
            
    return render_template_string(HTML_TEMPLATE, schedule=schedule)

@app.route('/delete/<int:index>', methods=['POST'])
def delete_entry(index):
    if 0 <= index < len(schedule):
        del schedule[index]
        save_schedule()
    return redirect(url_for('schedule_page'))

@app.route('/replace_audio/<int:index>', methods=['POST'])
def replace_audio(index):
    if 0 <= index < len(schedule):
        audio_file = request.files.get('audio_file')
        if audio_file and allowed_file(audio_file.filename):
            old_audio_path = schedule[index].get('audio_file_path')
            if old_audio_path and os.path.exists(old_audio_path):
                os.remove(old_audio_path)

            filename = secure_filename(audio_file.filename)
            new_audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(new_audio_file_path)

            schedule[index]['audio_file_path'] = new_audio_file_path
            save_schedule()
    return redirect(url_for('schedule_page'))

# Новый маршрут для редактирования времени
@app.route('/edit_time/<int:index>', methods=['POST'])
def edit_time(index):
    if 0 <= index < len(schedule):
        lesson_start = request.form.get('lesson_start')
        lesson_end = request.form.get('lesson_end')
        if lesson_start and lesson_end:
            schedule[index]['lesson_start'] = lesson_start
            schedule[index]['lesson_end'] = lesson_end
            save_schedule()
    return redirect(url_for('schedule_page'))

if __name__ == '__main__':
    threading.Thread(target=check_schedule, daemon=True).start()
    app.run(debug=True)
