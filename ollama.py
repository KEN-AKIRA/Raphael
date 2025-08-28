import os
import time
import datetime
from dotenv import load_dotenv
import requests
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
from PIL import Image
import cv2
from config_prompt import get_raphael_prompt

load_dotenv()  # Baca file .env dan set environment variables


def ask_ollama(prompt, model="phi3:mini"):
    try:
        messages = get_raphael_prompt(prompt)

        # ubah format biar sesuai dengan Ollama
        ollama_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            ollama_messages.append({"role": role, "content": content})

        payload = {
            "model": model,
            "messages": ollama_messages,
            "options": {
                "temperature": 0.7,
                "num_predict": 1000
            },
            "stream": False  # ini kunci biar nggak JSONL
        }

        response = requests.post(
            "http://localhost:11434/api/chat",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            return data["message"]["content"]
        else:
            print("[Ollama Error]", response.status_code, response.text)
            return None

    except Exception as e:
        print(f"[Ollama Exception] {e}")
        return None
    

# -------- BLIP Image Captioning -------- #
local_model_path = "C:/Users/pc-i5/Desktop/Entitas destop/models/blip-image-captioning-base"

processor = BlipProcessor.from_pretrained(local_model_path, use_fast=True)
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


# -------- Main -------- #
if __name__ == "__main__":
    response = ask_ollama(
        "Ceritakan secara ringkas, namun mendalam, tentang pentingnya kecepatan dalam model bahasa seperti LLM.",
        model="phi3:mini"  # pastikan model sudah di-pull di Ollama
    )
    print("Response from Ollama:")
    print(response)
