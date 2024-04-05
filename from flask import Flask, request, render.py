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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Расписание школьных звонков</title>
    <style>
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        background-color: #f0f0f0;
    }
    .container {
        max-width: 800px; /* Можно отрегулировать, если требуется */
        margin: auto;
        padding: 20px;
        background-color: white;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    }
    h1, h2 {
        color: #333;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    table, th, td {
        border: 1px solid #ddd;
    }
    th, td {
        padding: 10px;
        text-align: left;
    }
    th {
        background-color: #f2f2f2;
    }
    .btn {
        display: inline-block;
        padding: 8px 15px; /* Уменьшаем отступы */
        font-size: 0.9rem; /* Уменьшаем размер шрифта */
        color: white;
        background-color: #007bff;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        text-decoration: none;
        margin-top: 45px; /* Отступ сверху, чтобы опустить кнопку ниже на 1.5 см */
    }
    .btn-danger {
        background-color: #dc3545;
    }
    .btn-small {
        padding: 5px 10px;
        font-size: 0.8rem;
    }
    form {
        margin: 0;
    }
</style>

</head>
<body>
    <div class="container">
        <h1 id="current_time">Загрузка времени...</h1>
        <h2 id="current_date">Загрузка даты...</h2>
        <h2>Расписание звонков</h2>
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
        function updateDateTime() {
            var now = new Date();
            var hours = now.getHours().toString().padStart(2, '0');
            var minutes = now.getMinutes().toString().padStart(2, '0');
            var seconds = now.getSeconds().toString().padStart(2, '0');
            var year = now.getFullYear();
            var month = (now.getMonth() + 1).toString().padStart(2, '0');
            var day = now.getDate().toString().padStart(2, '0');

            document.getElementById('current_time').innerText = hours + ':' + minutes + ':' + seconds;
            document.getElementById('current_date').innerText = year + '-' + month + '-' + day;
        }

        setInterval(updateDateTime, 1000);
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
            # Проверяем, совпадает ли текущее время с началом или концом урока
            if now == time_slot['lesson_start'] or now == time_slot['lesson_end']:
                audio_file_path = time_slot['audio_file_path']  # Путь к аудиофайлу для воспроизведения
                play_sound(audio_file_path)  # Воспроизводим аудио
                # Ждем некоторое время перед следующей проверкой, чтобы избежать повторного воспроизведения
                time.sleep(120)
                break  # Выходим из цикла, если аудиофайл уже воспроизведен
        time.sleep(2)  # Краткая пауза перед следующей проверкой расписания


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
            
    current_time = datetime.now().strftime('%H:%M:%S')
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template_string(HTML_TEMPLATE, schedule=schedule, current_time=current_time, current_date=current_date)

@app.route('/delete/<int:index>', methods=['POST'])
def delete_entry(index):
    if 0 <= index < len(schedule):
        del schedule[index]
        save_schedule()  # Save the updated schedule to file
    return redirect(url_for('schedule_page'))

if __name__ == '__main__':
    threading.Thread(target=check_schedule, daemon=True).start()
    app.run(debug=True)
