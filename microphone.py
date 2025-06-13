import speech_recognition as sr

def test_microphone():
    print("Daftar mikrofon yang tersedia:")
    mic_list = sr.Microphone.list_microphone_names()
    for i, mic_name in enumerate(mic_list):
        print(f"{i}: {mic_name}")

    device_index = int(input("\nPilih nomor mikrofon yang ingin diuji: "))

    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1.8  # Atur ambang batas kepekaan

    try:
        with sr.Microphone(device_index=device_index) as source:
            print("Kalibrasi noise ambient selama 1 detik, harap diam...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            print("Mulai merekam, silakan bicara...")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
            print("Merekam selesai, memproses suara...")

        text = recognizer.recognize_google(audio, language="id-ID")
        print(f"Hasil pengenalan suara: {text}")

    except sr.WaitTimeoutError:
        print("⏰ Waktu tunggu habis, tidak ada suara yang didengar.")
    except sr.UnknownValueError:
        print("❌ Tidak dapat mengenali suara.")
    except sr.RequestError as e:
        print(f"❌ Gagal menghubungi layanan pengenalan suara; {e}")
    except Exception as e:
        print(f"❌ Terjadi error: {e}")

if __name__ == "__main__":
    test_microphone()
    input("\nTekan Enter untuk keluar...")
