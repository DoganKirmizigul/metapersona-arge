import requests
import pandas as pd
from datetime import datetime

# Google Places API için API anahtarınızı buraya ekleyin
API_KEY = 'AIzaSyB9MLfHsr1Md2CAo2MjyzzpQZiN73yTpGs'
place_id = 'ChIJu7meXwiQwxQRf_D18DMeZIk'  # Text Search API ile aldığınız place_id'yi buraya ekleyin

# Place Details API URL (yorumları Türkçe almak için language=tr ekleniyor)
place_details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}&language=tr'

# Place Details API isteği
response = requests.get(place_details_url)
data = response.json()

# Yorumları saklamak için liste
reviews = []

# Yorumları işleme
if data.get('status') == 'OK' and 'reviews' in data['result']:
    for review in data['result']['reviews']:
        text = review.get('text', '')
        rating = review.get('rating', 'N/A')  # Yorumdaki puan
        timestamp = review.get('time', 0)
        review_date = datetime.fromtimestamp(timestamp)

        # Yorumları listeye ekle
        reviews.append([review_date.strftime('%Y-%m-%d'), rating, text])

# Yorumları yazdırma veya kaydetme
if reviews:
    df = pd.DataFrame(reviews, columns=['Date', 'Rating', 'Review'])
    df.to_excel('hotel_reviews.xlsx', index=False)
    print(f"{len(reviews)} yorum 'hotel_reviews.xlsx' dosyasına yazdırıldı.")
else:
    print("Yorum bulunamadı.")
