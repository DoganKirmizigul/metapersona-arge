import re
from deep_translator import GoogleTranslator

# Metni 5000 karakterlik parçalara bölen bir fonksiyon
def split_text(text, max_length=5000):
    chunks = []
    while len(text) > max_length:
        # En son boşluktan keserek bölme işlemi yap
        split_at = text.rfind(' ', 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return chunks

# Metinden özel karakterleri temizleme fonksiyonu
def clean_text(text):
    # Özel karakterleri ve emojileri temizler
    cleaned_text = re.sub(r'[^\w\s,.!?]', '', text)
    return cleaned_text

# Dosyayı aç ve oku
with open('aska_lara.txt', 'r', encoding='utf-8') as file:
    turkce_metin = file.read()

# Metni temizle
cleaned_turkce_metin = clean_text(turkce_metin)

# Metni parçalara böl
chunks = split_text(cleaned_turkce_metin)

# Parçaları sırayla çevir ve birleştir
translated_text = ''
translator = GoogleTranslator(source='tr', target='en')
for chunk in chunks:
    try:
        translated_text += translator.translate(chunk)
    except Exception as e:
        print(f"Hata: {e} - Parça çevrilemiyor: {chunk}")

# Çevirilen metni yazdır
print("Çevrilen metin:\n", translated_text)

# Çevirilen metni bir dosyaya yaz
with open('cevrilen_metin.txt', 'w', encoding='utf-8') as output_file:
    output_file.write(translated_text)

print("Çevirilen metin 'cevrilen_metin.txt' dosyasına kaydedildi.")
