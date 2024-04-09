import time
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import pygame

#pygame.mixer.init()


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/audio'  # Путь для сохранения аудио файлов
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'ogg'}
app.secret_key = 'your_secret_key'
schedule_file = 'schedule.json'  # Путь к файлу с расписанием

played_slots = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_schedule(schedule):
    with open(schedule_file, 'w') as f:
        json.dump(schedule, f)

def load_schedule():
    try:
        with open(schedule_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    
import pygame
from datetime import datetime
import time
import os

def play_audio_once(file_path):
    """Воспроизведение аудиофайла с ожиданием его окончания."""
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # Ожидание окончания воспроизведения
        time.sleep(1)
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()

def play_scheduled_audio():
    pygame.mixer.init()
    while True:
        now = datetime.now().strftime('%H:%M')
        schedule = load_schedule()
        for index, slot in enumerate(schedule):
            lesson_start = slot['lesson_start']
            lesson_end = slot['lesson_end']
            audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], slot['audio_file_path'])

            # Воспроизведение в начале урока
            if now == lesson_start and not played_slots.get(index, {}).get('start', False):
                play_audio_once(audio_file_path)
                if index not in played_slots:
                    played_slots[index] = {}
                played_slots[index]['start'] = True  # Отмечаем, что воспроизведение на начало занятия выполнено

            # Воспроизведение в конце урока
            elif now == lesson_end and not played_slots.get(index, {}).get('end', False):
                play_audio_once(audio_file_path)
                if index not in played_slots:
                    played_slots[index] = {}
                played_slots[index]['end'] = True  # Отмечаем, что воспроизведение на окончание занятия выполнено

        time.sleep(2)  # Периодическая проверка расписания


@app.route('/')
def index():
    schedule = load_schedule()
    return render_template('index.html', schedule=schedule)

@app.route('/add', methods=['POST'])
def add_time_slot():
    schedule = load_schedule()
    if request.method == 'POST':
        lesson_start = request.form['lesson_start']
        lesson_end = request.form['lesson_end']
        audio_file = request.files['audio_file']

        if audio_file and allowed_file(audio_file.filename):
            filename = secure_filename(audio_file.filename) # type: ignore
            audio_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(audio_file_path)
            schedule.append({
                'lesson_start': lesson_start,
                'lesson_end': lesson_end,
                'audio_file_path': filename
            })
            save_schedule(schedule)
            flash('Новый звонок успешно добавлен.', 'success')
        else:
            flash('Ошибка добавления: неверный формат файла.', 'error')

    return redirect(url_for('index'))


@app.route('/delete/<int:index>', methods=['POST'])
def delete_time_slot(index):
    schedule = load_schedule()
    try:
        audio_file_path = schedule[index]['audio_file_path']
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], audio_file_path)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], audio_file_path))
        del schedule[index]
        save_schedule(schedule)
        flash('Звонок успешно удалён.', 'success')
    except (IndexError, FileNotFoundError):
        flash('Ошибка удаления: звонок не найден.', 'error')

    return redirect(url_for('index'))

@app.route('/edit_time/<int:index>', methods=['POST'])
def edit_time(index):
    schedule = load_schedule()
    if request.method == 'POST':
        try:
            schedule[index]['lesson_start'] = request.form['lesson_start']
            schedule[index]['lesson_end'] = request.form['lesson_end']
            save_schedule(schedule)
            flash('Время звонка успешно изменено.', 'success')
        except IndexError:
            flash('Ошибка изменения: звонок не найден.', 'error')

    return redirect(url_for('index'))

@app.route('/replace_audio/<int:index>', methods=['POST'])
def replace_audio(index):
    schedule = load_schedule()
    if request.method == 'POST':
        audio_file = request.files['audio_file']
        if audio_file and allowed_file(audio_file.filename):
            filename = secure_filename(audio_file.filename) # type: ignore
            old_file_path = schedule[index]['audio_file_path']
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], old_file_path)):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], old_file_path))
            audio_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            schedule[index]['audio_file_path'] = filename
            save_schedule(schedule)
            flash('Аудио файл успешно заменён.', 'success')
        else:
            flash('Ошибка замены аудио: неверный формат файла.', 'error')

    return redirect(url_for('index'))

@app.route('/move_up/<int:index>', methods=['POST'])
def move_up(index):
    schedule = load_schedule()  # Загружаем расписание
    if index > 0 and index < len(schedule):  # Убедимся, что индекс в допустимом диапазоне
        # Меняем элементы местами
        schedule[index], schedule[index - 1] = schedule[index - 1], schedule[index]
        save_schedule(schedule)  # Сохраняем изменённое расписание
    else:
        flash('Ошибка перемещения: некорректный индекс.', 'error')
    return redirect(url_for('index'))  # Используем маршрут 'index' для перенаправления

@app.route('/move_down/<int:index>', methods=['POST'])
def move_down(index):
    schedule = load_schedule()  # Загружаем расписание
    if index >= 0 and index < len(schedule) - 1:  # Убедимся, что индекс в допустимом диапазоне
        # Меняем элементы местами
        schedule[index], schedule[index + 1] = schedule[index + 1], schedule[index]
        save_schedule(schedule)  # Сохраняем изменённое расписание
    else:
        flash('Ошибка перемещения: некорректный индекс.', 'error')
    return redirect(url_for('index'))  # Используем маршрут 'index' для перенаправления

from threading import Thread

if __name__ == '__main__':
    audio_thread = Thread(target=play_scheduled_audio)
    audio_thread.start()
    app.run(debug=False)