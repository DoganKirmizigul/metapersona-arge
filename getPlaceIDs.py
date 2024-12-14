import requests
import pandas as pd

API_KEY = 'AIzaSyB9MLfHsr1Md2CAo2MjyzzpQZiN73yTpGs'

hotel_list_df = pd.read_excel('hotel_list.xlsx')
hotel_names = hotel_list_df['name']

results = []

for hotel in hotel_names:
    query = f'{hotel}'
    url = f'https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={API_KEY}'

    response = requests.get(url)
    data = response.json()

    if data.get('status') == 'OK' and len(data['results']) > 0:
        place_id = data['results'][0]['place_id']
        address = data['results'][0].get('formatted_address', 'N/A')
        results.append([hotel, place_id, address])
    else:
        results.append([hotel, 'N/A', 'N/A'])

results_df = pd.DataFrame(results, columns=['Hotel Name', 'Place ID', 'Address'])
results_df.to_excel('hotel_place_ids.xlsx', index=False)

print("Otel listesi ve place_id'ler 'hotel_place_ids.xlsx' dosyasına yazdırıldı.")
