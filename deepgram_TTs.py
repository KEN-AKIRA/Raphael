import requests

API_KEY = ""
text_to_speak = "Halo, ini adalah suara dari Deepgram."

# URL dengan parameter di query string
url = (
    "https://api.deepgram.com/v1/speak"
    "?model=aura-2-theia-en"
    "&encoding=linear16"
    "&sample_rate=16000"
)

response = requests.post(
    url,
    headers={
        "Authorization": f"Token {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "text": text_to_speak
    }
)

# Simpan hasil audio
if response.status_code == 200:
    with open("output_audio.wav", "wb") as f:
        f.write(response.content)
    print("✅ Audio berhasil disimpan sebagai output_audio.wav")
else:
    print("❌ Gagal menghasilkan TTS:", response.status_code, response.text)
