from transformers import BlipProcessor, BlipForConditionalGeneration
from ultralytics import YOLO
import easyocr
import cv2
from PIL import Image
import numpy as np

local_model_path = "C:/Users/pc-i5/Desktop/Entitas destop/models/blip-image-captioning-base"

processor = BlipProcessor.from_pretrained(local_model_path, use_fast=True)
model = BlipForConditionalGeneration.from_pretrained(local_model_path)



yolo_model = YOLO("models/yolov8n.pt")
ocr_reader = easyocr.Reader(['en'], gpu=False)

def capture_frame():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None

def describe_with_blip(image_np):
    image_pil = Image.fromarray(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB))
    inputs = processor(images=image_pil, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption

def detect_objects_yolo(image_np):
    results = yolo_model(image_np)
    objects = set()
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls)
            label = r.names[cls_id]
            objects.add(label)
    return list(objects)

def read_text_easyocr(image_np):
    results = ocr_reader.readtext(image_np)
    texts = [text for (_, text, conf) in results if conf > 0.5]
    return texts

def analyze_camera_scene(question):
    print("[INFO] Mengambil gambar dari kamera...")
    image = capture_frame()
    if image is None:
        print("[ERROR] Tidak bisa menangkap gambar.")
        return None

    print("[INFO] Menganalisis dengan BLIP...")
    caption = describe_with_blip(image)
    print("[BLIP Deskripsi]:", caption)

    print("[INFO] Mendeteksi objek dengan YOLO...")
    objects = detect_objects_yolo(image)
    print("[Deteksi Objek]:", objects)

    print("[INFO] Membaca tulisan dengan EasyOCR...")
    texts = read_text_easyocr(image)
    print("[Tulisan Terdeteksi]:", texts)

    full_description = f"{caption}.\n"
    if objects:
        full_description += f"Terdapat objek: {', '.join(objects)}.\n"
    if texts:
        full_description += f"Tulisan terbaca: {', '.join(texts)}."

    return full_description
