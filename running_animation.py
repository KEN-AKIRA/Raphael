import tkinter as tk
from PIL import Image, ImageTk, UnidentifiedImageError
import os

# === KONFIGURASI ===
FRAME_DURATION = 200  # ms
ANIM_FOLDER = "run_frames"
SCALE = 0.5
TRANSPARENT_COLOR = "black"

# === SETUP WINDOW TRANSPARAN ===
root = tk.Tk()
root.overrideredirect(True)
root.wm_attributes("-topmost", True)
root.configure(bg=TRANSPARENT_COLOR)
root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)

# === FUNGSI LOAD FRAME ===
def load_frames(folder):
    frames = []
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith(".png"):
            filepath = os.path.join(folder, filename)
            try:
                img = Image.open(filepath).convert("RGBA")
                img = img.resize(
                    (int(img.width * SCALE), int(img.height * SCALE)),
                    Image.Resampling.LANCZOS
                )
                frames.append(ImageTk.PhotoImage(img))
            except UnidentifiedImageError:
                print(f"[ERROR] File gambar rusak atau tidak bisa dibaca: {filename}")
            except Exception as e:
                print(f"[ERROR] Tidak bisa load {filename}: {e}")
    return frames

frames = load_frames(ANIM_FOLDER)

if not frames:
    print("[FATAL] Tidak ada frame yang berhasil dimuat!")
    root.destroy()
    exit()

frame_index = 0

# === CANVAS ===
canvas = tk.Canvas(root, width=frames[0].width(), height=frames[0].height(),
                   bg=TRANSPARENT_COLOR, highlightthickness=0)
canvas.pack()

# Sprite awal
sprite = canvas.create_image(0, 0, anchor="nw", image=frames[0])

# === UPDATE ANIMASI ===
def update_animation():
    global frame_index
    canvas.itemconfig(sprite, image=frames[frame_index % len(frames)])
    frame_index += 1
    root.after(FRAME_DURATION, update_animation)

update_animation()
root.mainloop()
