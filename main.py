import os
import re
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import time
from vision import analyze_camera_scene
from openrouter import ask_openai, describe_image
import threading
import requests
from pydub import AudioSegment
from pydub.playback import play
import io
import pygame
import tempfile
import cv2
import datetime
import time
import json
import os

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





FRAME_DURATION = 200
SCALE = 0.3
#DRAG_LOOP_COUNT = 1

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

#entry bergaya klasic
entry = tk.Entry(root, width=40, bg=bg_color, fg=fg_color, font="Ariel", relief="ridge", bd=4, insertbackground=fg_color)

entry.pack(pady=10)

# Tombol bergaya klasik
btn = tk.Button(root, text="Raphael", command=lambda: on_submit(), 
                bg=button_color, fg="white", font=medieval_font,
                relief="raised", bd=4, activebackground=highlight)
btn.pack()

def on_submit():
    question = entry.get()
    if question.strip():
        ask_ai_and_talk(question)
        entry.delete(0, tk.END)

# === SETUP CANVAS ===
canvas = tk.Canvas(root, width=idle_frames[0].width(), height=idle_frames[0].height(),
                   bg=TRANSPARENT_COLOR, highlightthickness=0)
canvas.pack()
sprite = canvas.create_image(0, 0, anchor="nw", image=idle_frames[0])

# === 3. Inisialisasi UI Energi ===



#energy_ui = EnergyUI(root)  # ⬅️ PENGHUBUNG ENERGY_UI


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


face_detected = False
last_detect_time = None


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

    
# def on_mouse_motion(event):
    # global is_shy, shy_frame_index, last_interaction_time

    
    # character_coords = canvas.coords(sprite)
    # relative_x = event.x - character_coords[0]
    # relative_y = event.y - character_coords[1]


    # Deteksi dada untuk malu (misalnya y antara 100 dan 150)
    # if not is_shy and 100 <= relative_y <= 150 and 50 <= relative_x <= 150:
        # is_shy = True
        # shy_frame_index = 0
        # start_shy()

    last_interaction_time = time.time()

def play_idle_animation():
    canvas.itemconfig(sprite, image=idle_frames[0])



# === ANIMASI UTAMA ===
def update_frame():
    global frame_index
    global is_starting, start_frame_index
    global is_shy, shy_frame_index
    global is_talking
    global mouth_talk_index
    
    #now = time.time()


    # status = energy_ui.get_status()
    # is_sleeping = energy_ui.is_sleeping

    if is_starting:
         if start_frame_index < len(start_frames):
             canvas.itemconfig(sprite, image=start_frames[start_frame_index])
             start_frame_index += 1
             root.after(FRAME_DURATION, update_frame)    
             return   
            
         else:
             is_starting = False
             frame_index = 0



    # Prioritas: shy
    # if is_shy:
        # global shy_frame_index
        # if shy_frame_index < len(shy_frames):
            # canvas.itemconfig(sprite, image=shy_frames[shy_frame_index])
            # shy_frame_index += 1
        # else:
        #    is_shy = False
            # shy_frame_index = 0
        # root.after(FRAME_DURATION, update_frame)
        # return
    
    if is_talking:
        root.after(FRAME_DURATION, update_frame)
        return

    
    else:
        frame_index +=1
        canvas.itemconfig(sprite, image=idle_frames[frame_index % len(idle_frames)])
        root.after(FRAME_DURATION, update_frame)



def capture_frame():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Camera Error] Tidak bisa membuka kamera")
        return None
    ret, frame = cap.read()
    cap.release()
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
        threading.Thread(target=speak_with_deepgram, args=(response,), daemon=True).start()


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

    **Jangan memulai percakapan dari awal, lanjutkan saja. Gunakan gaya bahasa yang sesuai dengan pengguna sebelumnya.**
    """


    response = ask_openai(prompt)
    print("[RESPON OPENAI]:", response)
    if response:
        add_to_history("user", question)
        add_to_history("assistant", response)
        threading.Thread(target=speak_with_deepgram, args=(response,), daemon=True).start()


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
            "melihat"
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

Gunakan informasi di atas untuk melanjutkan percakapan secara natural, **jangan menebak objek spesifik yang tidak pasti terlihat**.
Jika kamu tidak yakin dengan objeknya, cukup beri komentar umum yang tetap ramah dan nyambung dengan percakapan terakhir.
Gunakan bahasa yang sama dengan pengguna terakhir, dan jangan memulai percakapan dari awal.

Balas dengan satu paragraf singkat, tidak lebih dari 3 kalimat.
"""
            response = ask_openai(prompt)

            if response:
                process_vision_response(response)
                time.sleep(10)

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


DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")


def speak_with_deepgram(text):
    if not DEEPGRAM_API_KEY:
        print("API Key tidak ditemukan")
        return

    url = (
        "https://api.deepgram.com/v1/speak"
        "?model=aura-2-amalthea-en"
        "&encoding=mp3"
    )
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    json_data = {"text": text}

    try:
        response = requests.post(url, headers=headers, json=json_data)
        if response.status_code == 200:
            audio_data = io.BytesIO(response.content)
            sound = AudioSegment.from_file(audio_data, format="mp3")

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


def stop_talking():
    global is_talking
    is_talking = False
    canvas.itemconfig(sprite, image=idle_frames[0])



def update_mouth_animation():
    global is_talking, mouth_talk_index
    #now = time.time()
    try:
        if is_talking and pygame.mixer.get_init() and pygame.mixer.music.get_busy():

            canvas.itemconfig(sprite, image=mouth_talk_frames[mouth_talk_index % len(mouth_talk_frames)])
            mouth_talk_index += 1
            root.after(300, update_mouth_animation)
        else:
            stop_talking()
    except pygame.error as e:
        print(f"[ Animasi mouth Error] {e}")
        stop_talking()

def start_talking(response_text):
    global is_talking, mouth_talk_index
    mouth_talk_index = 0
    is_talking = True
    #duration_ms = max(20000, len(response_text) * 50)
    #duration_ms = 20000
    #talk_end_time = time.time() + duration_ms / 1000
    print("Raphael:", response_text)
    root.after(200, update_mouth_animation)

def ask_ai_and_talk(question, as_role="user"):
    def worker():

        full_prompt = ""  # inisialisasi dulu
        # tambahkan obrolan ke history
        add_to_history("user", question)

        # gabungkan semua history agar response bisa diambil
        chat_history = get_chat_history()
        
        for entry in chat_history:
            prefix = "User: " if entry["role"] == "user" else "Assistant: "
            full_prompt += prefix + entry["content"] + "\n"

        response = ask_openai(full_prompt.strip())
        if response:
            add_to_history("assistent", response)

            #start_talking(response)
            threading.Thread(target=speak_with_deepgram, args=(response,), daemon=True).start()
        else:
            error_msg = "Maaf, saya tidak bisa menjawab pertanyaan Anda saat ini."
            add_to_history("assistent", error_msg)
            start_talking(error_msg)
            threading.Thread(target=speak_with_deepgram, args=("gagal mendapatkan response dari AI",), daemon=True).start()
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

#energy_ui = EnergyUI(
    #root,
   
    #sleep_start_callback=start_sleep,
   #sleep_stop_callback=stop_sleep
#)



# Kirim fungsi ke EnergyUI
#energy_ui = EnergyUI(
    #root,
    
#)

def start_shy():
    global shy_frame_index
    shy_frame_index = 0



# === BIND EVENT ===
canvas.bind("<ButtonPress-1>", start_move)
canvas.bind("<B1-Motion>", do_move)
# canvas.bind("<Motion>", on_mouse_motion)
canvas.bind("<ButtonRelease-1>", end_move)



# Dapatkan ukuran layar
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Ukuran karakter (jendela aplikasi)
root.update_idletasks()  # Agar winfo_width & winfo_height valid
window_width = root.winfo_width()
window_height = root.winfo_height()

# Update posisi agar lebih ke kiri dan ke bawah
x_offset = -170  # geser ke kiri 100 piksel
y_offset = 10  # geser lebih ke bawah (nilai negatif agar makin ke atas)

# Hitung posisi untuk bawah tengah layar
x = (screen_width - window_width) // 2 + x_offset
y = screen_height - window_height - 50 + y_offset # 50 px di atas taskbar, bisa kamu ubah

# Atur posisi jendela
root.geometry(f"+{x}+{y}")


#threading.Thread(target=start_camera_vision, daemon=True).start()

vision_thread = threading.Thread(target=run_vision_openai_loop, daemon=True)
vision_thread.start()

# === JALANKAN LOOP ===
update_frame()
root.mainloop()
