import cv2
from groq_client import ask_groq
# Load model face detection dari OpenCV
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def detect_faces(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    return faces

# Fungsi mock untuk mengirim prompt ke AI, ganti dengan implementasi aslimu
def ask_groq(prompt):
    # Contoh jawaban AI (bisa diganti dengan API call yang kamu pakai)
    if "seseorang" in prompt:
        return "Halo! Senang bertemu denganmu!"
    else:
        return "."

def main():
    cap = cv2.VideoCapture(0)  # buka kamera
    if not cap.isOpened():
        print("Gagal membuka kamera")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Gagal membaca frame dari kamera")
            break

        faces = detect_faces(frame)
        if len(faces) > 0:
            prompt = "Saya melihat seseorang di depan kamera. Sapaan apa yang cocok?"
        else:
            prompt = "."

        response = ask_groq(prompt)
        print("AI Response:", response)

        # Gambar kotak di wajah yang terdeteksi (optional)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 0), 2)

        cv2.putText(frame, response, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow("Camera", frame)

        # Tekan 'q' untuk keluar
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
