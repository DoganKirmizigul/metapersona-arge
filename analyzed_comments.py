import requests
import pandas as pd
from datetime import datetime
import time

# Google Places API için API anahtarınızı buraya ekleyin
API_KEY = 'AIzaSyB9MLfHsr1Md2CAo2MjyzzpQZiN73yTpGs'
place_id = 'ChIJu7meXwiQwxQRf_D18DMeZIk'  # İlgili otelin place_id'sini buraya ekleyin

# Place Details API URL (yorumları Türkçe almak için language=tr ekleniyor)
url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}&language=tr'

# Sonuçları saklamak için liste
reviews = []

# İlk API isteğini gönder
response = requests.get(url)
data = response.json()

# İlk sayfadaki yorumları işleme
if data.get('status') == 'OK' and 'reviews' in data['result']:
    for review in data['result']['reviews']:
        text = review.get('text', '')
        timestamp = review.get('time')
        review_date = datetime.fromtimestamp(timestamp)

        # Yorumları listeye ekle
        reviews.append([review_date.strftime('%Y-%m-%d'), text])

    # `next_page_token` varsa, sonraki sayfalara geçmek için kullanacağız
    next_page_token = data.get('next_page_token')

    # Yorumları alabilecek kadar almaya çalışıyoruz
    while next_page_token:
        time.sleep(2)  # `next_page_token`'ın geçerli olabilmesi için biraz beklemek gerekir (2 saniye)
        next_url = f'https://maps.googleapis.com/maps/api/place/details/json?pagetoken={next_page_token}&key={API_KEY}&language=tr'
        next_response = requests.get(next_url)
        next_data = next_response.json()

        # Sonraki sayfadaki yorumları ekle
        if next_data.get('status') == 'OK' and 'reviews' in next_data['result']:
            for review in next_data['result']['reviews']:
                text = review.get('text', '')
                timestamp = review.get('time')
                review_date = datetime.fromtimestamp(timestamp)

                # Yorumları listeye ekle
                reviews.append([review_date.strftime('%Y-%m-%d'), text])

            # Yeni `next_page_token` al
            next_page_token = next_data.get('next_page_token')
        else:
            break  # Eğer `next_page_token` yoksa veya sorun oluştuysa döngüyü bitir

# Yorumları Excel dosyasına yazdırma
if reviews:
    df = pd.DataFrame(reviews, columns=['Date', 'Review'])
    df.to_excel('hotel_reviews.xlsx', index=False)
    print(f"{len(reviews)} yorum 'hotel_reviews.xlsx' dosyasına yazdırıldı.")
else:
    print("Yorum bulunamadı.")
