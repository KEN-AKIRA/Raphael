import requests
from bs4 import BeautifulSoup

def scrape_internasional_cnn():
    url = "https://www.cnnindonesia.com/internasional"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    daftar = []

    # Temukan semua elemen <span class="flex-grow">
    for box in soup.select("span.flex-grow"):
        judul_el = box.select_one("h1")
        isi_el = box.select_one("span.text-sm")

        if judul_el and isi_el:
            judul = judul_el.get_text(strip=True)
            isi = isi_el.get_text(strip=True)
            daftar.append({
                "title": judul,
                "snippet": isi
            })

    return daftar[:5]  # ambil 5 berita terbaru

# Uji coba
if __name__ == "__main__":
    hasil = scrape_internasional_cnn()
    for item in hasil:
        print(f"📌 {item['title']}\n   {item['snippet']}\n")
