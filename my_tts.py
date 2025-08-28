import requests
import os
import pygame
import time

def tts(text):
    ref_path = "C:/Users/pc-i5/Desktop/gpt_tts/rafaclone.wav"

    if not os.path.exists(ref_path):
        print("[ERROR] Referensi suara tidak ditemukan.")
        return

    response = requests.post("http://127.0.0.1:9880/tts", json={
        "text": text,                   # str.(required) text to be synthesized
        "text_lang": "ja",               # str.(required) language of the text to be synthesized
        "ref_audio_path": ref_path,         # str.(required) reference audio path
        "aux_ref_audio_paths": [],    # list.(optional) auxiliary reference audio paths for multi-speaker synthesis           # str.(optional) prompt text for the reference audio
        "prompt_lang": "ja",            # str.(required) language of the prompt text for the reference audio
        "top_k": 5,                   # int. top k sampling
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
        if os.path.exists("output.wav"):
            try:
                os.remove("output.wav")
            except PermissionError:
               print("[ERROR] File terkunci. Menunggu...")
               time.sleep(1)
               os.remove("output.wav")     

        with open("output.wav", "wb") as f:
            f.write(response.content)
        print("[INFO] Audio berhasil dibuat.")
        
        pygame.mixer.init()
        pygame.mixer.music.load("output.wav")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
    else:
        print(f"[ERROR] Gagal TTS: {response.status_code} {response.text}")
