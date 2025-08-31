import os
import re
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import time
from vision import analyze_camera_scene
from openrouter import ask_openai, describe_image
#from ollama import ask_ollama, describe_image
import threading
import requests
from pydub import AudioSegment
from pydub.playback import play
import io
import pygame
import tempfile
import cv2
import datetime
import json
import os
import speech_recognition as sr
from weather import get_local_weather
from website_international_cnn import scrape_internasional_cnn
import psutil
import tempfile
import wave
from deep_translator import GoogleTranslator
import signal
import sys




translator = GoogleTranslator(source='en', target='id')
sr.Microphone()

USER_DATA_FILE = "user.json"
MAX_HISTORY = 50

# global variable untuk menyimpan data user saat runtime
user_data = {}

def load_user_data():
    global user_data
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {"chat_history": []}
                if "chat_history" not in data:
                    data["chat_history"] = []
                user_data = data
            except json.JSONDecodeError:
                user_data = {"chat_history": []}
    else:
        user_data = {"chat_history": []}

def save_user_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=2)

def add_to_history(role, content, source=None):
    user_data["chat_history"].append({"role": role, "content": content})
    user_data["chat_history"] = user_data["chat_history"][-MAX_HISTORY:]
    save_user_data()

def get_chat_history():
    return user_data["chat_history"]

# saat program mulai, panggil ini supaya user_data terisi
load_user_data()



pygame.mixer.init()

# Load the face detection cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')




# === KONFIGURASI ===
IDLE_FOLDER = "idle_frames"
DRAG_FOLDER = "drag_frames"

START_FOLDER = "start_frames"

SHY_FOLDER = "shy_frames"

MOUTH_TALK_FOLDER = "mouth_talk_frames"
LAUGH_FOLDER = "laugh_frames"
MOUTH_FOLDER = "mouth_frames"
IDLE2_FOLDER = "idle2_frames"
IDLE3_FOLDER = "idle3_frames"
IDLE4_FOLDER = "idle4_frames"

# === INISIALISASI VARIABEL ===

listening = False

# Atur speed or slow motion
FRAME_DURATION = 200
MOUTH_DURATION = 190
LAUGH_DURATION = 200

# === DURASI FRAME BERBEDA ===
FRAME_DURATION_IDLE1 = 200   # ms, idle pertama
FRAME_DURATION_IDLE2 = 110   # ms, idle kedua
FRAME_DURATION_IDLE3 = 110
FRAME_DURATION_IDLE4 = 110

# === FRAME MOUTH ===
FRAME_MOUTH = 110

# ukuran karakter
SCALE = 0.5

IDLE_TIMEOUT = 80_000


last_interaction_time = time.time()

# === FUNGSI LOAD FRAME ===
def load_frames(folder):
    frames = []
    
    def extract_number(filename):
        match = re.search(r'\d+', filename)
        return int(match.group()) if match else 0

    files = sorted([f for f in os.listdir(folder) if f.endswith(".png")], key=extract_number)

    for filename in files:
        filepath = os.path.join(folder, filename)
        try:
            print(f"Loading: {filename}")
            img = Image.open(filepath).convert("RGBA")
            img = img.resize((int(img.width * SCALE), int(img.height * SCALE)), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(img))
        except Exception as e:
            print(f"[ERROR] Gagal memuat {filename}: {e}")

    return frames


# fungsi untuk mendifinisikan audio efek
def audio_efek_async(audio_path="audio.mp3"):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        print("✔audio berhasil dikirim")
    except Exception as e:
        print(f"audio sedang Error {e}")

def play_audio(audio_path="audio.mp3"):
    threading.Thread(target=audio_efek_async, args=(audio_path,), daemon=True).start()
        

# Fungsi Real-time Listening
def listen_loop():
    print("[DEBUG] Memulai listen_loop...")
    global listening
    recognizer = sr.Recognizer()
    mic_index = 5  # ganti dengan indeks mic 

    try:
        mic = sr.Microphone(device_index=mic_index)
        print(f"[DEBUG] Menggunakan microphone: {mic_index} - {mic.list_microphone_names()[mic_index]}")
    except Exception as e:
        print(f"[ERROR] Gagal mengakses microphone: {e}")
        listening = False
        return

    recognizer.dynamic_energy_threshold = False  # NON-AUTO
    recognizer.energy_threshold = 50  # Nilai kecil = lebih sensitif (default sekitar 300)
    recognizer.pause_threshold = 0.9  # jeda bicara lebih singkat
    recognizer.non_speaking_duration = 0.1  # waktu minimum tanpa suara

    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        print("🎤 Mode real-time aktif...")

    last_input_time = time.time()
    timeout_duration = 120

    while listening:

        if time.time() - last_input_time > timeout_duration:
            print("⏳ Tidak ada input selama 2 menit. Kembali ke passive mode.")
            stop_listening()
            break

        with mic as source:
            if not listening:
                break
            print("🎤 Dengarkan...")
            try:
                audio = recognizer.listen(source, timeout=10)
                text = recognizer.recognize_google(audio, language="id-ID")
                print(f"[STT] Kamu bilang: {text}")

                last_input_time = time.time()

                if "stop" in text:
                    print("⏹️ Mendengar 'stop', mematikan mode real-time.")
                    stop_listening()
                    break

                entry.delete(0, tk.END)
                entry.insert(0, text)
                on_submit()  # ganti dengan aksi respons 

            except sr.WaitTimeoutError:
                print("⏳ Tidak terdengar suara.")
            except sr.UnknownValueError:
                print("😕 Tidak bisa mengenali suara.")
            except sr.RequestError as e:
                print(f"[ERROR] STT gagal: {e}")


# Passive Wake Word Listener
def passive_wake_listener():
    try:
        global listening
        print("[DEBUG] Memulai passive_wake_listener...")
        recognizer = sr.Recognizer()
        mic = sr.Microphone(device_index=5)  # ganti dengan indeks mic 

        with mic as source:
            try:
                print("🔊 Mengakses microphone...")
                recognizer.adjust_for_ambient_noise(source)
                print("🕯️ Menunggu kata kunci 'raphael'...")
            except Exception as e:
                print(f"[ERROR] Gagal mengakses microphone: {e}")
                return

        while True:
            if listening:
                break  # keluar dari loop jika sudah dalam mode real-time
            with mic as source:
                try:
                    audio = recognizer.listen(source, timeout=5)
                    text = recognizer.recognize_google(audio, language="id-ID").lower()
                    print(f"[Passive Listener] Terdeteksi: {text}")

                    if any(keyword in text for keyword in ["raphael", "rafael", "ra", "rafa"]):
                        # Jika mendeteksi kata kunci "raphael", mulai mode real-time
                        print("🔊 'Raphael' terdengar! Mode bicara aktif!")
                        # panggil audio effek
                        play_audio("audio.mp3")
                        start_listening_thread()
                        break # hentikan passive listener saat realtime mulai

                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    print(f"[ERROR Passive] STT gagal: {e}")
                    continue
    except Exception as e:
        print(f"[ERROR Passive Listener] {e}")
        # threading.Thread(target=passive_wake_listener, daemon=True).start()  # Restart listener jika error
        


# Tombol untuk mulai mode real-time
def start_listening_thread():
    global listening
    if not listening:
        listening = True
        print("[DEBUG] Memulai thread listen_loop")
        print("[info] daftar microphone yang tersedia:")
        for i, mic_name in enumerate(sr.Microphone.list_microphone_names()):
            print(f"Mic {i}: {mic_name}")
        # Mulai thread untuk mendengarkan suara
        threading.Thread(target=listen_loop, daemon=True).start()

def stop_listening():
    global listening
    listening = False
    print("⏹️ Mode real-time dimatikan.")
    threading.Thread(target=passive_wake_listener, daemon=True).start()  # Mulai passive listener lagi




# === INISIALISASI TKINTER ===
TRANSPARENT_COLOR = "black"
root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-topmost", True)
root.configure(bg=TRANSPARENT_COLOR)
root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)



# === LOAD FRAME ===
idle_frames = load_frames(IDLE_FOLDER)
drag_frames = load_frames(DRAG_FOLDER)

start_frames = load_frames(START_FOLDER)

shy_frames = load_frames(SHY_FOLDER)

mouth_talk_frames = load_frames(MOUTH_TALK_FOLDER)
laugh_frames = load_frames(LAUGH_FOLDER)
mouth_frames = load_frames(MOUTH_FOLDER)
idle2_frames = load_frames(IDLE2_FOLDER)
idle3_frames = load_frames(IDLE3_FOLDER)
idle4_frames = load_frames(IDLE4_FOLDER)

#===============================================
# === WIDGETS DAN STYLING ===


# === TOMBOL MODERN ===
def style_modern_button(btn, normal_bg, hover_bg):
    btn.config(
        relief="flat",        # biar rata (flat)
        bd=0,                 # tanpa border
        bg=normal_bg,
        fg="white",
        activebackground=hover_bg,
        activeforeground="white",
        font=("Segoe UI", 12, "bold"),
        padx=15, pady=8
    )
    # efek hover
    def on_enter(e): btn.config(bg=hover_bg)
    def on_leave(e): btn.config(bg=normal_bg)
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)

# Ganti definisi tombol lama pakai ini

# Buat frame khusus untuk tombol biar sejajar
btn_frame = tk.Frame(root, bg="black")  # bg biar nyatu sama root kalau perlu
btn_frame.pack(pady=5)

voice_btn = tk.Button(btn_frame, text="🔊 Speak", command=start_listening_thread)
voice_btn.pack(side="left", padx=5)
style_modern_button(voice_btn, normal_bg="#4199a9", hover_bg="#0AF511")

stop_btn = tk.Button(btn_frame, text="⏹️ Stop", command=stop_listening)
stop_btn.pack(side="left", padx=5)
style_modern_button(stop_btn, normal_bg="#5E1A1A", hover_bg="#26dc51")



#warna dan font gaya klasik

bg_color = "#f5e1a4"
fg_color = "#4b2e0f" 
button_color = "#a67c52"  
highlight = "#d4af37"

#tanbah font
try:
    medieval_font = ("old English Text MT", 14)
except:
    medieval_font = ("Ariel", 14, "italic")

# Entry bergaya klasik dengan placeholder
placeholder = "Ask anything..."
entry = tk.Entry(root, width=40, bg=bg_color, fg=fg_color, font="Arial", 
                 relief="ridge", bd=4, insertbackground=fg_color)
entry.pack(pady=10)

# Set placeholder awal
entry.insert(0, placeholder)
entry.config(fg="grey")  # warna abu-abu biar kayak transparan

def on_focus_in(event):
    if entry.get() == placeholder:
        entry.delete(0, tk.END)
        entry.config(fg=fg_color)

def on_focus_out(event):
    if entry.get() == "":
        entry.insert(0, placeholder)
        entry.config(fg="grey")

entry.bind("<FocusIn>", on_focus_in)
entry.bind("<FocusOut>", on_focus_out)


entry.bind("<Return>", lambda event: on_submit())


# Tombol bergaya klasik
btn = tk.Button(root, text="Raphael", command=lambda: on_submit(), 
                bg=button_color, fg="white", font=medieval_font,
                relief="raised", bd=4, activebackground=highlight)
btn.pack(pady=10)

# Tambahkan efek hover manual
def on_enter(e):
    btn["background"] = "#06eaff"  # warna saat hover

def on_leave(e):
    btn["background"] = button_color  # balik ke warna asli

btn.bind("<Enter>", on_enter)
btn.bind("<Leave>", on_leave)

def on_submit():
    question = entry.get()
    if question.strip():
        ask_ai_and_talk(question)
        entry.delete(0, tk.END)

# === SETUP CANVAS ===
canvas = tk.Canvas(root, width=idle_frames[0].width(), height=idle_frames[0].height(),
                   bg=TRANSPARENT_COLOR, highlightthickness=0)
canvas.pack()


# === Koordinat mulut untuk idle 1 & idle 2 ===
MOUTH_OFFSET_IDLE1 = (-1, -1)  # (X, Y) untuk idle 1
MOUTH_OFFSET_IDLE2 = (-1, -1 )  # (X, Y) untuk idle 2
MOUTH_OFFSET_IDLE3 = (-7, -1 )  # (X, Y) untuk idle 3
MOUTH_OFFSET_IDLE4 = (-1, -1 )  # (X, Y) untuk idle 4



sprite = canvas.create_image(0, 0, anchor="nw", image=idle_frames[0])
 #setup mouth
# Layer khusus mulut talk (kosong dulu)
mouth_talk_sprite = canvas.create_image(0, 0, anchor="nw")




# === STATUS VARIABEL ===
is_mouse_down = False
frame_index = 0

is_starting = True
start_frame_index = 0

is_shy = False
shy_frame_index = 0

is_talking = False
mouth_talk_index = 0
talk_end_time = 0

is_laugh = False
frame_index = 0

#is_mouth = False
#mouth_index = 0

frame_index = 0
idle_state = 1  # 1 = idle pertama, 2 = idle kedua

face_detected = False
last_detect_time = None

current_animation = None  # Untuk menyimpan ID root.after

#translator = Translator()

# === EVENT DRAG ===
def start_move(event):
    global is_mouse_down, last_interaction_time
    is_mouse_down = True
    last_interaction_time = time.time()
    root.x = event.x_root
    root.y = event.y_root

    
def do_move(event):
    dx = event.x_root - root.x
    dy = event.y_root - root.y
    root.geometry(f"+{root.winfo_x() + dx}+{root.winfo_y() + dy}")
    root.x = event.x_root
    root.y = event.y_root

def end_move(event):
    global is_mouse_down, last_interaction_time
    
    is_mouse_down = False
    last_interaction_time = time.time()

    
def on_mouse_motion(event):
    global is_shy, shy_frame_index, last_interaction_time

    
    character_coords = canvas.coords(sprite)
    relative_x = event.x - character_coords[0]
    relative_y = event.y - character_coords[1]


    # Deteksi oppai untuk shy (misalnya y antara 100 dan 150)
    if not is_shy and 350 <= relative_y <= 400 and 50 <= relative_x <= 150:
        is_shy = True
        shy_frame_index = 0
        start_shy()

    last_interaction_time = time.time()

def play_idle_animation():
    canvas.itemconfig(sprite, image=idle_frames[0])


print("[RAM] Usage:", psutil.virtual_memory().percent, "%")

# Animasi utama
def update_frame():
    global frame_index, idle_state
    global is_starting, start_frame_index
    global is_shy, shy_frame_index
    global is_talking
    global mouth_talk_index
    global is_laugh
    #global is_mouth
    #global mouth_index
    


    # Animasi awal
    if is_starting:
        if start_frame_index < len(start_frames):
            canvas.itemconfig(sprite, image=start_frames[start_frame_index])
            start_frame_index += 1
            root.after(FRAME_DURATION, update_frame)
            return
        else:
            is_starting = False
            frame_index = 0

    # Prioritas 1: Animasi malu (shy)
    if is_shy:
        if shy_frame_index < len(shy_frames):
            canvas.itemconfig(sprite, image=shy_frames[shy_frame_index])
            shy_frame_index += 1
        else:
            is_shy = False
            shy_frame_index = 0
        root.after(FRAME_DURATION, update_frame)
        return

    # Prioritas 2: Animasi ketawa
    if is_laugh:
        if frame_index < len(laugh_frames):
            canvas.itemconfig(sprite, image=laugh_frames[frame_index])
            frame_index += 1
        else:
            is_laugh = False
            frame_index = 0
        root.after(LAUGH_DURATION, update_frame)
        return

    # Prioritas 3: Animasi bicara (update dilakukan di update_mouth_animation)
    #if is_talking:
        #root.after(FRAME_DURATION, update_frame)
        #return

    # Prioritas 4: Animasi bicara (update dilakukan di update_mouth_animation / update_mouth_talk_animation)
    #if is_talking or is_mouth:
        #root.after(FRAME_DURATION, update_frame)
        #return  # Jangan update idle saat mouth aktif
    if is_talking:
        pass


    # Default: idle
    #canvas.itemconfig(sprite, image=idle_frames[frame_index % len(idle_frames)])
    #frame_index += 1
    #root.after(FRAME_DURATION, update_frame)

      
    # === IDLE SYSTEM ===
    if idle_state == 1:
        canvas.itemconfig(sprite, image=idle_frames[frame_index % len(idle_frames)])
        canvas.coords(mouth_talk_sprite, MOUTH_OFFSET_IDLE1[0], MOUTH_OFFSET_IDLE1[1])
        delay = FRAME_DURATION_IDLE1
    elif idle_state == 2:
        canvas.itemconfig(sprite, image=idle2_frames[frame_index % len(idle2_frames)])
        canvas.coords(mouth_talk_sprite, MOUTH_OFFSET_IDLE2[0], MOUTH_OFFSET_IDLE2[1])
        delay = FRAME_DURATION_IDLE2
    elif idle_state == 3:
        canvas.itemconfig(sprite, image=idle3_frames[frame_index % len(idle3_frames)])
        canvas.coords(mouth_talk_sprite, MOUTH_OFFSET_IDLE3[0], MOUTH_OFFSET_IDLE3[1])
        delay = FRAME_DURATION_IDLE3
    elif idle_state == 4:
        canvas.itemconfig(sprite, image=idle4_frames[frame_index % len(idle4_frames)])
        canvas.coords(mouth_talk_sprite, MOUTH_OFFSET_IDLE4[0], MOUTH_OFFSET_IDLE4[1])
        delay = FRAME_DURATION_IDLE4

    frame_index += 1

    if idle_state == 1 and frame_index >= len(idle_frames):
        idle_state = 2
        frame_index = 0
    elif idle_state == 2 and frame_index >= len(idle2_frames):
        idle_state = 3
        frame_index = 0
    elif idle_state == 3 and frame_index >= len(idle3_frames):
        idle_state = 4
        frame_index = 0
    elif idle_state == 4 and frame_index >= len(idle4_frames):
        idle_state = 1
        frame_index = 0

    root.after(delay, update_frame)



# Global camera
cap = cv2.VideoCapture(1)

def capture_frame():
    global cap
    if not cap.isOpened():
        print("[Camera Error] Tidak bisa membuka kamera")
        return None
    ret, frame = cap.read()
    if not ret:
        print("[Camera Error] Gagal membaca frame")
        return None
    return frame

def get_time_context():
    hour = datetime.datetime.now().hour
    if hour < 11:
        return "pagi"
    elif hour < 17:
        return "siang"
    elif hour < 21:
        return "sore"
    else:
        return "malam"
    
def format_chat_history(chat_history):
    lines = []
    for entry in chat_history:
        role = entry.get("role", "user").capitalize()  # User / Assistant
        content = entry.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def process_vision_response(response):
    if response:
        add_to_history("assistent", response, source="vision")
        threading.Thread(target=tts, args=(response,), daemon=True).start()




# vision realtime untuk bertanya 
def ask_about_camera_image(question):
    print("[INFO] Mengambil gambar dari kamera untuk pertanyaan:", question)
    image = capture_frame()
    if image is None:
        print("[ERROR] Tidak bisa menangkap gambar dari kamera.")
        return

    description = analyze_camera_scene(question)
    print("[DESKRIPSI GAMBAR]:", description)

    chat_history = get_chat_history()  # ambil dari memori
    full_chat_history_text = format_chat_history(chat_history)

    prompt = f"""
    Kamu adalah Raphael, asisten AI pribadi yang ramah, ekspresif, dan komunikatif. Kamu memiliki memori dari percakapan sebelumnya dengan pengguna.

    Berikut adalah ringkasan percakapan sebelumnya:
    {full_chat_history_text}

    Sekarang, pengguna menunjukkan sesuatu melalui kamera dan bertanya:
    "{question}"

    Deskripsi otomatis dari gambar yang kamu lihat:
    "{description}"

    Tugasmu:
    - Beri komentar tentang apa yang kamu lihat dari gambar tersebut, seolah-olah kamu benar-benar melihatnya.
    - Hubungkan responmu dengan konteks percakapan sebelumnya jika memungkinkan.
    - Jika objek dalam gambar tidak jelas atau tidak spesifik, tetap tanggapi secara ramah dan sopan tanpa membuat asumsi liar.
    - Responmu harus singkat (maksimal 3 kalimat), hangat, dan terasa personal, seperti teman yang memperhatikan.
    - Use English for response user

    **Jangan memulai percakapan dari awal, lanjutkan saja. Gunakan gaya bahasa yang sesuai dengan pengguna sebelumnya.**
    """


    response = ask_openai(prompt)
    print("[RESPON OPENAI]:", response)
    # ✅ Tambahkan translate di sini
    try:
        translated = GoogleTranslator(source='en', target='id').translate(response)
        print(f"[Translate]: {translated}")
    except Exception as e:
        print("[Translate Error]", e)
        translated = response  # fallback

    if response:
        add_to_history("user", question)
        add_to_history("assistant", response)
        threading.Thread(target=tts, args=(response,), daemon=True).start()


def on_submit():
    question = entry.get()
    if question.strip():
        lowered = question.lower()
        camera_keywords = [
            "ini apa",
            "apa ini",
            "lihat aku",
            "coba lihat aku",
            "tolong lihat aku",
            "kamera hidup",
            "aktifkan kamera",
            "lihat wajahku",
            "apakah aku terlihat",
            "buka kamera sekarang",
            "lihat",
            "komentari",
            "look",
            "melihat",
            "analisis",
            "analisa"
        ]
        # Cek apakah pertanyaan mengandung kata kunci kamera
        # jika ada, panggil fungsi untuk menangkap gambar dari kamera
        if any(keyword in lowered for keyword in camera_keywords):
            ask_about_camera_image(question)
        else:
            ask_ai_and_talk(question)
        entry.delete(0, tk.END)


# vision auto response
def run_vision_openai_loop():
    global face_detected, last_detect_time
    while True:
        print("\n[INFO] Mengambil frame dari kamera...")
        image = capture_frame()
        if image is None:
            print("[ERROR] Gagal ambil frame, coba lagi...")
            time.sleep(5)
            continue

        caption = describe_image(image)
        print("[Caption]:", caption)

        face_detected = detect_face(image)
        print("[Face Detected?]", face_detected)

        if face_detected:
            emotion = detect_emotion(image) or "netral"
            print("[Ekspresi Detected]:", emotion)

            time_context = get_time_context()

            chat_history = get_chat_history()  # ambil dari memori
            full_chat_history_text = format_chat_history(chat_history)


            prompt = f"""
Kamu adalah Raphael, asisten AI yang ramah dan komunikatif. Kamu ingat percakapan sebelumnya dengan pengguna.

Berikut ini adalah riwayat percakapan:
{full_chat_history_text}

Saat ini kamu melihat pengguna melalui kamera:
- Deskripsi visual (hasil computer vision): {caption}
- Ekspresi wajah pengguna: {emotion}
- Waktu sekarang: {time_context}
- Use English for response user

Gunakan informasi di atas untuk melanjutkan percakapan secara natural, **jangan menebak objek spesifik yang tidak pasti terlihat**.
Jika kamu tidak yakin dengan objeknya, cukup beri komentar umum yang tetap ramah dan nyambung dengan percakapan terakhir.
Gunakan bahasa yang sama dengan pengguna terakhir, dan jangan memulai percakapan dari awal.

Balas dengan satu paragraf singkat, tidak lebih dari 3 kalimat.
"""
            response = ask_openai(prompt)

            if response:

                # ✅ Tambahkan translate di sini
                try:
                    translated = GoogleTranslator(source='en', target='id').translate(response)
                    print(f"[Translate]: {translated}")
                except Exception as e:
                    print("[Translate Error]", e)
                    translated = response  # fallback

                process_vision_response(response)  # tetap pakai respons asli (English)
                time.sleep(10)
                #process_vision_response(response)
                #time.sleep(10)

        else:
            print("[INFO] Tidak ada wajah terdeteksi, skip...")
        
        time.sleep(300)

 

def detect_face(image):
    if image is None:
        return False

    # Gunakan OpenCV Haar Cascade
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

    # DEBUG: tampilkan deteksi wajah
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (255, 0, 0), 2)
    cv2.imshow("Detected Face", image)
    cv2.waitKey(1000)  # tunggu 1 detik
    cv2.destroyAllWindows()

    return len(faces) > 0


def detect_emotion(image):
    # Dummy, bisa diganti DeepFace/MediaPipe model
    return "senang"  # misal hardcoded dulu




def tts(text):
    ref_path = "C:/Users/pc-i5/Desktop/gpt_tts/ciel_kawai.mp3"

    if not os.path.exists(ref_path):
        print("[ERROR] Referensi suara tidak ditemukan.")
        return

    try:
        response = requests.post("http://127.0.0.1:9880/tts", json={
        "text": text,                   # str.(required) text to be synthesized
        "text_lang": "en",               # str.(required) language of the text to be synthesized
        "ref_audio_path": ref_path,         # str.(required) reference audio path
        "aux_ref_audio_paths": [],    # list.(optional) auxiliary reference audio paths for multi-speaker synthesis           # str.(optional) prompt text for the reference audio
        "prompt_lang": "en",            # str.(required) language of the prompt text for the reference audio
        "top_k": 7,                   # int. top k sampling
        "top_p": 1,                   # float. top p sampling
        "temperature": 1,             # float. temperature for sampling
        "text_split_method": "cut3",  # str. text split method, see text_segmentation_method.py for details.
        "batch_size": 1,              # int. batch size for inference
        "batch_threshold": 0.75,      # float. threshold for batch splitting.
        "split_bucket": True,          # bool. whether to split the batch into multiple buckets.
        "speed_factor":1.0,           # float. control the speed of the synthesized audio.
        "fragment_interval":0.3,      # float. to control the interval of the audio fragment.
        "seed": -1,                   # int. random seed for reproducibility.
        "media_type": "wav",          # str. media type of the output audio, support "wav", "raw", "ogg", "aac".
        "streaming_mode": False,      # bool. whether to return a streaming response.
        "parallel_infer": True,       # bool.(optional) whether to use parallel inference.
        "repetition_penalty": 1.35,   # float.(optional) repetition penalty for T2S model.
        "sample_steps": 32,           # int. number of sampling steps for VITS model V3.
        "super_sampling": False,       # bool. whether to use super-sampling for audio when using VITS model V3.

    })
        if response.status_code == 200:
            audio_data = io.BytesIO(response.content)
            sound = AudioSegment.from_file(audio_data, format="wav")

            #duration_ms = len(sound)
           

            # Simpan ke file sementara
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                temp_path = f.name
                sound.export(temp_path, format="wav")

            # Mainkan dengan pygame
            # pygame.mixer.init()
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            start_talking(text)
            # while pygame.mixer.music.get_busy():
                # time.sleep(0.1)
                #start_talking di panggil after pygame.
            

            #root.after(200, lambda: start_talking(text))

        else:
            print("TTS Error:", response.status_code, response.text)
    except Exception as e:
        print(f"[TTS Error] {e}")



def stop_current_animation():
    global current_animation
    try:
        if current_animation:
            root.after_cancel(current_animation)
            current_animation = None
    except Exception as e:
        print(f"[Stop Animation Error] {e}")




def stop_talking():
    global is_talking
    is_talking = False
    #canvas.itemconfig(sprite, image=idle_frames[0])
     # Hapus mulut talk saat berhenti bicara
    canvas.itemconfig(mouth_talk_sprite, image="")

def update_laugh_animation():
    global is_laugh, is_mouth, is_talking, frame_index, current_animation
    # 🔹 Matikan animasi lain
    #is_mouth = False
    #is_talking = False
    try:
        if frame_index and pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            canvas.itemconfig(sprite, image=laugh_frames[frame_index % len(laugh_frames)])
            frame_index += 1
            current_animation = root.after(200, update_laugh_animation)
        else:
            is_laugh = False
    except pygame.error as e:
        print(f"[Animasi Laugh Error] {e}")
        is_laugh = False



def update_mouth_talk_animation():
    global is_talking, mouth_talk_index, current_animation
    #now = time.time()
    try:
        if is_talking and pygame.mixer.get_init() and pygame.mixer.music.get_busy():

            canvas.itemconfig(mouth_talk_sprite, image=mouth_talk_frames[mouth_talk_index % len(mouth_talk_frames)])
            mouth_talk_index += 1
            root.after(FRAME_MOUTH, update_mouth_talk_animation)
        else:
            canvas.itemconfig(mouth_talk_sprite, image="")  # hapus mulut saat selesai
            stop_talking()
    except pygame.error as e:
        print(f"[ Animasi mouth Error] {e}")
        stop_talking()



#def update_mouth_animation():
    #global is_mouth, mouth_index, current_animation

    # 🔹 Cegah tumpang tindih dengan animasi ketawa
    #if is_laugh:
        #return

    #try:
        #if is_mouth and pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            #canvas.itemconfig(sprite, image=mouth_frames[mouth_index % len(mouth_frames)])
            #mouth_index += 1
            #current_animation = root.after(200, update_mouth_animation)
        #else:
            #is_mouth = False
    #except pygame.error as e:
        #print(f"[Animasi mulut Error] {e}")
        #is_mouth = False



def start_talking(response_text):
    global is_talking, is_laugh, is_mouth
    response_lower = response_text.strip().lower()
    stop_current_animation()  # hentikan animasi sebelumnya


    # Reset semua
    is_laugh = False
    #is_talking = False
    #is_mouth = False

    # Hanya tertawa
    if response_lower == "hahaha":
        is_laugh = True
        start_laugh_animation()
    
    # Tertawa lalu bicara
    elif "hahaha" in response_lower:
        #is_laugh = True

        #def after_laugh_then_mouth():
            #if not is_laugh:
                # Mulai animasi mouth setelah laugh selesai
                #start_mouth_animation()
            #else:
                #root.after(200, after_laugh_then_mouth)
        def start_talking_after_laugh(response_text):
            def check_laugh_then_talk():
                if not is_laugh:
                    start_mouth_talk_animation()
                else:
                    root.after(100, check_laugh_then_talk)
            check_laugh_then_talk()

        start_laugh_animation()
        #after_laugh_then_mouth()
        start_talking_after_laugh(response_text)
    # Bicara langsung
    else:
        start_mouth_talk_animation()


def start_mouth_talk_animation():
    global is_talking, mouth_talk_index
    stop_current_animation()  # Hentikan animasi lain
    is_talking = True
    mouth_talk_index = 0
    update_mouth_talk_animation()

#def start_mouth_animation():
    #global is_mouth, mouth_index
    #stop_current_animation()  # Hentikan animasi lain
    #is_mouth = True
    #mouth_index = 0
    #update_mouth_animation()

def start_laugh_animation():
    global is_laugh, frame_index
    stop_current_animation()  # Hentikan animasi lain
    is_laugh = True
    #is_mouth = False
    #is_talking = False
    frame_index = 0
    print("😆 Raphael tertawa...")
    root.after(200, update_laugh_animation)


#def ask_ai_and_talk(question, as_role="user"):
    #def worker():

        #weather_info = None
        #news_info = None
        
        #if "cuaca" in question.lower():
            #weather_info = get_local_weather()
            
           
        #elif any(word in question.lower() for word in ["berita", "news"]):
            #print("Ambil berita terbaru")
            #try:
                #news_info = scrape_internasional_cnn()
            #except Exception as e:
                #print("[Error] gagal mengambil data web scraping", e)
                #news_info = "Berita tidak tersidia saat ini atau gagal mengambil data berita"

       
        #full_prompt = ""  # inisialisasi dulu
        # tambahkan obrolan ke history
        #add_to_history("user", question)

        # gabungkan semua history agar response bisa diambil
        #chat_history = get_chat_history()
        
        #for entry in chat_history:
            #prefix = "User: " if entry["role"] == "user" else "Assistant: "
            #full_prompt += prefix + entry["content"] + "\n"

        # 3. Tambahkan catatan tambahan (cuaca / berita)
        #if weather_info or news_info:
            #full_prompt += "\n---\nCatatan untuk asisten:\n"
        #if weather_info:
            #if news_info:
            #full_prompt += f"- Berita internasional terbaru tahun 2025: {news_info}\n"

        #start = time.time()
        #response = ask_openai(full_prompt.strip())
        #print("[DEBUG] Waktu respons AI:", time.time() - start, "detik")

        #if response:
            #add_to_history("assistent", response)

            
            #start_talking(response)
            #threading.Thread(target=tts, args=(response,), daemon=True).start()
        #else:
            #error_msg = "Maaf, saya tidak bisa menjawab pertanyaan Anda saat ini."
            #add_to_history("assistent", error_msg)
            #start_talking(error_msg)
            #threading.Thread(target=tts, args=("gagal mendapatkan response dari AI",), daemon=True).start()
    #threading.Thread(target=worker, daemon=True).start()

def ask_ai_and_talk(question, as_role="user"):
    def worker():
        weather_info = None
        news_info = None
        
        # Cek cuaca atau berita
        if "cuaca" in question.lower():
            weather_info = get_local_weather()
        elif any(word in question.lower() for word in ["berita", "news"]):
            print("Ambil berita terbaru")
            try:
                news_info = scrape_internasional_cnn()
            except Exception as e:
                print("[Error] gagal mengambil data web scraping", e)
                news_info = "Berita tidak tersedia saat ini atau gagal mengambil data berita"

        # Simpan ke history
        add_to_history("user", question)
        chat_history = get_chat_history()

        # Gabungkan history
        full_prompt = ""
        for entry in chat_history:
            prefix = "User: " if entry["role"] == "user" else "Assistant: "
            full_prompt += prefix + entry["content"] + "\n"

        # Tambahkan info cuaca/berita
        if weather_info or news_info:
            full_prompt += "\n---\nCatatan untuk asisten:\n"
        if weather_info:
            full_prompt += f"- Informasi cuaca saat ini: {weather_info}\n"
        if news_info:
            full_prompt += f"- Berita internasional terbaru tahun 2025: {news_info}\n"

        # ✅ Tambahkan instruksi anti-*...* di akhir
        full_prompt += "\n\nInstruksi penting untuk Assistant:\n"
        "1. Jangan menulis aksi atau ekspresi fisik dalam tanda bintang (*...*).\n"
        "2. Hapus semua tanda bintang jika ada.\n"
        "3. Jangan pernah menampilkan reasoning internal atau teks dalam <think>...</think>.\n"
        "4. Fokus hanya pada percakapan langsung, tanpa narasi atau deskripsi tindakan.\n"
        "5. Jawaban harus singkat, relevan dengan pertanyaan terakhir pengguna, "
        "dan tidak bertele-tele.\n"
        "6. Ikuti instruksi ini pada setiap jawaban tanpa terkecuali."

        # Minta respons dari AI
        start = time.time()
        response = ask_openai(full_prompt.strip())
        print("[DEBUG] Waktu respons AI:", time.time() - start, "detik")

        if response:
            add_to_history("assistent", response)

            # Terjemahkan respons
            try:
                translated = GoogleTranslator(source='en', target='id').translate(response)
                print(f"[Translate]: {translated}")
            except Exception as e:
                print("[Translate Error]", e)
                translated = response  # fallback

            # Jalankan TTS pakai hasil terjemahan
            threading.Thread(target=tts, args=(response,), daemon=True).start()

        else:
            error_msg = "Maaf, saya tidak bisa menjawab pertanyaan Anda saat ini."
            add_to_history("assistent", error_msg)
            threading.Thread(target=tts, args=(error_msg,), daemon=True).start()

    threading.Thread(target=worker, daemon=True).start()



# start_talking di panggil setelah pygame sudah siap

def start_sleep():
    global is_sleeping, sleep_frame_index, last_interaction_time
    if not is_sleeping:
        is_sleeping = True
        sleep_frame_index = 0
        last_interaction_time = time.time()
        print("karakter sleep")

def stop_sleep():
    global is_sleeping, sleep_frame_index
    is_sleeping = False
    sleep_frame_index = 0


def start_shy():
    global is_shy, shy_frame_index
    shy_frame_index = 0


# === BIND EVENT ===
canvas.bind("<ButtonPress-1>", start_move)
canvas.bind("<B1-Motion>", do_move)
canvas.bind("<Motion>", on_mouse_motion)
canvas.bind("<ButtonRelease-1>", end_move)


# Dapatkan ukuran layar
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Ukuran karakter (jendela aplikasi)
root.update_idletasks()  # Agar winfo_width & winfo_height valid
window_width = root.winfo_width()
window_height = root.winfo_height()

# Update posisi agar lebih ke kiri dan ke bawah
x_offset = -760  # geser ke kiri 100 piksel
y_offset = 490  # geser lebih ke bawah (nilai negatif agar makin ke atas)

# Hitung posisi untuk bawah tengah layar
x = (screen_width - window_width) // 2 + x_offset
y = screen_height - window_height - 50 + y_offset # 50 px di atas taskbar

# Atur posisi jendela
root.geometry(f"+{x}+{y}")


#threading.Thread(target=start_camera_vision, daemon=True).start()

vision_thread = threading.Thread(target=run_vision_openai_loop, daemon=True)
vision_thread.start()
print("[DEBUG] Memulai passive_wake_listener thread...")
threading.Thread(target=passive_wake_listener, daemon=True).start()
print("[DEBUG] passive_wake_listener thread dijalankan.")

# === JALANKAN LOOP ===
#update_frame()
#root.mainloop()

def handle_exit(sig, frame):
    print("\n[EXIT] Menutup aplikasi...")
    try:
        if cap and cap.isOpened():
            cap.release()  # lepas kamera
            print("[INFO] Kamera dilepas")
    except:
        pass

    try:
        pygame.mixer.quit()  # stop audio
        print("[INFO] Pygame mixer dimatikan")
    except:
        pass

    try:
        root.destroy()  # tutup Tkinter
        print("[INFO] Tkinter GUI ditutup")
    except:
        pass

    sys.exit(0)

# pasang handler Ctrl+C
signal.signal(signal.SIGINT, handle_exit)

# === jalankan tkinter mainloop dengan aman ===
try:
    update_frame()  # jalankan animasi
    root.mainloop()
except KeyboardInterrupt:
    handle_exit(None, None)
