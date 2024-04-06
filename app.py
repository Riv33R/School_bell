from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import threading
import time
from datetime import datetime
import pygame
import json

app = Flask(__name__)

UPLOAD_FOLDER = "uploaded_files"
ALLOWED_EXTENSIONS = {"mp3", "wav", "ogg"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

pygame.mixer.init()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


schedule_file = "schedule.json"

try:
    with open(schedule_file, "r") as file:
        schedule = json.load(file)
except FileNotFoundError:
    schedule = []


def play_sound(audio_file_path):
    pygame.mixer.music.load(audio_file_path)
    pygame.mixer.music.play()


def check_schedule():
    while True:
        now = datetime.now().strftime("%H:%M")
        for time_slot in schedule:
            if now == time_slot["lesson_start"] or now == time_slot["lesson_end"]:
                audio_file_path = time_slot["audio_file_path"]
                play_sound(audio_file_path)
                time.sleep(120)
                break
        time.sleep(2)


def save_schedule():
    with open(schedule_file, "w") as file:
        json.dump(schedule, file)


@app.route("/", methods=["GET", "POST"])
def schedule_page():
    if request.method == "POST":
        lesson_start = request.form.get("lesson_start")
        lesson_end = request.form.get("lesson_end")
        audio_file = request.files.get("audio_file")

        if (
            lesson_start
            and lesson_end
            and audio_file
            and allowed_file(audio_file.filename)
        ):
            filename = secure_filename(audio_file.filename)  # type: ignore
            audio_file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            audio_file.save(audio_file_path)

            schedule.append(
                {
                    "lesson_start": lesson_start,
                    "lesson_end": lesson_end,
                    "audio_file_path": audio_file_path,
                }
            )
            save_schedule()

        return redirect(url_for("schedule_page"))

    return render_template("index.html", schedule=schedule)


@app.route("/move_up/<int:index>", methods=["POST"])
def move_up(index):
    if index > 0:  # Проверяем, что элемент не первый в списке
        schedule[index], schedule[index - 1] = (
            schedule[index - 1],
            schedule[index],
        )  # Меняем местами с предыдущим
        save_schedule()
    return redirect(url_for("schedule_page"))


@app.route("/move_down/<int:index>", methods=["POST"])
def move_down(index):
    if index < len(schedule) - 1:  # Проверяем, что элемент не последний в списке
        schedule[index], schedule[index + 1] = (
            schedule[index + 1],
            schedule[index],
        )  # Меняем местами со следующим
        save_schedule()
    return redirect(url_for("schedule_page"))


@app.route("/delete/<int:index>", methods=["POST"])
def delete_entry(index):
    if 0 <= index < len(schedule):
        del schedule[index]
        save_schedule()
    return redirect(url_for("schedule_page"))


@app.route("/replace_audio/<int:index>", methods=["POST"])
def replace_audio(index):
    if 0 <= index < len(schedule):
        audio_file = request.files.get("audio_file")
        if audio_file and allowed_file(audio_file.filename):
            old_audio_path = schedule[index].get("audio_file_path")
            if old_audio_path and os.path.exists(old_audio_path):
                os.remove(old_audio_path)

            filename = secure_filename(audio_file.filename)  # type: ignore
            new_audio_file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            audio_file.save(new_audio_file_path)

            schedule[index]["audio_file_path"] = new_audio_file_path
            save_schedule()
    return redirect(url_for("schedule_page"))


# Новый маршрут для редактирования времени
@app.route("/edit_time/<int:index>", methods=["POST"])
def edit_time(index):
    if 0 <= index < len(schedule):
        lesson_start = request.form.get("lesson_start")
        lesson_end = request.form.get("lesson_end")
        if lesson_start and lesson_end:
            schedule[index]["lesson_start"] = lesson_start
            schedule[index]["lesson_end"] = lesson_end
            save_schedule()
    return redirect(url_for("schedule_page"))


if __name__ == "__main__":
    threading.Thread(target=check_schedule, daemon=True).start()
    app.run(debug=True)
