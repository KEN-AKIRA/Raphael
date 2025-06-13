import requests
from bs4 import BeautifulSoup

def get_local_weather():
    url = "https://weather.com/id-ID/weather/today/l/5d80e124dfc3a577d33f849cc90d3b66564140a8becc567de90a978f45eaa31d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Cari berdasarkan atribut data-testid
    temp_tag = soup.find("span", attrs={"data-testid": "TemperatureValue"})
    condition_tag = soup.find("div", attrs={"data-testid": "wxPhrase"})

    if temp_tag and condition_tag:
        temperature = temp_tag.text.strip()  # Contoh: "32°"
        condition = condition_tag.text.strip()  # Contoh: "Sebagian Berawan"
        return f"Cuaca saat ini: {temperature}, {condition}"
    else:
        return "Maaf, tidak bisa mengambil data cuaca."

# Tes
print(get_local_weather())
