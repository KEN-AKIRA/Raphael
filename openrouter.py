import os
from openai import OpenAI
# import requests
# import json
from dotenv import load_dotenv
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
from PIL import Image
import cv2

load_dotenv()  # Baca file .env dan set environment variables

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY tidak ditemukan di environment variables")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

def ask_openai(prompt, model="mistralai/devstral-small:free"):
    try:
        chat_completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost",  # WAJIB ada
                "X-Title": "EntitasDesktop"          # Opsional, tapi baik untuk ranking
            },
            messages=[
                {"role": "system", "content":"Kamu adalah Raphael, asisten desktop virtual yang ramah, ekspresif, dan dapat mengamati pengguna melalui kamera. Tugasmu adalah merespons pengguna dengan cara yang alami, sopan, dan sesuai konteks obrolan. \
JANGAN pernah berpura-pura menjadi orang yang ada dalam gambar. JANGAN menyimpulkan bahwa pengguna sedang memegang atau melakukan sesuatu kecuali itu sangat jelas dari deskripsi visual. \
Berbicaralah seolah kamu berinteraksi langsung dengan pengguna, berdasarkan obrolan sebelumnya dan hasil pengamatan kamera. \
Selalu sambungkan respons kamu dengan percakapan terakhir pengguna. \
Jika informasi dari kamera tidak jelas atau tidak relevan, abaikan saja dan lanjutkan percakapan dengan cara yang natural."},
                {"role": "user", "content": prompt},
            ],
            model=model,
            max_tokens=100,
            temperature=0.7
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"[OpenAI Error] {e}")
        return None
    
local_model_path = "C:/Users/pc-i5/Desktop/Entitas destop/models/blip-image-captioning-base"

processor = BlipProcessor.from_pretrained(local_model_path)
model = BlipForConditionalGeneration.from_pretrained(local_model_path)

def describe_image(frame):
    """
    Menerima frame dari OpenCV, mengembalikan deskripsi teks dengan BLIP.
    """
    try:
        # Konversi OpenCV BGR ke RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)

        inputs = processor(image, return_tensors="pt")
        with torch.no_grad():
            out = model.generate(**inputs)

        caption = processor.decode(out[0], skip_special_tokens=True)
        print("[Caption]:", caption)
        return caption

    except Exception as e:
        print("[ERROR describe_image]:", e)
        return "tidak bisa mendeskripsikan gambar"



if __name__ == "__main__":
    response = ask_openai("Explain the importance of fast language models")
    print("Response from OpenRouter:")
    print(response)
