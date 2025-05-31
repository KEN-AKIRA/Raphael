# Raphael - Asisten AI Interaktif Real-Time

**Raphael** adalah asisten AI cerdas dalam bentuk karakter anime yang mampu berinteraksi secara real-time melalui suara dan ekspresi visual. Dibangun menggunakan Python, OpenCV, Tkinter, dan teknologi pengenalan suara serta pengenalan wajah, Raphael menghadirkan pengalaman interaktif yang unik dan menyenangkan.

## 🎯 Fitur Utama

- 🎧 **Mendengar**: Mendeteksi dan memahami suara pengguna secara real-time.
- 🗣️ **Berbicara**: Memberikan respons suara alami menggunakan Text-to-Speech.
- 👁️ **Melihat wajah**: Mendeteksi wajah pengguna dan mengenali ekspresi.
- 😊 **Menunjukkan ekspresi**: Menampilkan ekspresi wajah anime yang sesuai secara responsif.
- 🧠 **Percakapan cerdas**: Menggunakan model AI untuk menjawab pertanyaan dan merespons konteks.
- 💬 **Riwayat percakapan**: Menyimpan interaksi agar bisa belajar dan beradaptasi.

## 🖼️ Antarmuka

Raphael muncul sebagai karakter anime di layar (menggunakan Tkinter), yang bisa bereaksi terhadap emosi dan input suara pengguna secara real-time.

## 🧰 Teknologi yang Digunakan

- Python 3.10+
- OpenCV (pengenalan wajah & kamera)
- Yolo (pengenalan objek)
- Blip (pengenalan keadaan)
- ocr (pengenalan teks)
- Tkinter (GUI)
- Deepgram API / Google Speech-to-Text (opsional untuk pengenalan suara)
- Deepgram / ElevanLabs (Text-to-Speech)
- OpenAI API (opsional, untuk pemrosesan bahasa alami)
- PIL / Pillow (manipulasi gambar ekspresi)
- json (simpan dan muat data percakapan)
- threading (untuk menjalankan beberapa tugas secara bersamaan)
- time (untuk mengatur waktu antar aksi)


## 🚀 Cara Menjalankan

1. **Klon repositori ini:**

```bash
git clone https://github.com/KEN-AKIRA/Raphael.git
cd Raphael
