import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import nltk

# Gerekli NLTK veri setlerini indir
nltk.download('stopwords')
nltk.download('wordnet')

def preprocess_text(text):
    # 1. Küçük harfe dönüştürme
    text = text.lower()
    
    # 2. Noktalama işaretlerini ve özel karakterleri kaldırma
    text = re.sub(r'[^\w\s]', '', text)
    
    # 3. Durdurma kelimelerini çıkarma
    stop_words = set(stopwords.words('turkish'))
    text = ' '.join([word for word in text.split() if word not in stop_words])
    
    # 4. Kök bulma (Stemming) ve lemmatization
    stemmer = PorterStemmer()
    lemmatizer = WordNetLemmatizer()
    text = ' '.join([lemmatizer.lemmatize(stemmer.stem(word)) for word in text.split()])
    
    # 5. Fazladan boşlukları temizleme
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
# Örnek kullanım
with open('palde_hotel.txt', 'r', encoding='utf-8') as file:  # encoding parametresi eklendi
    sample_text = file.read()
processed_text = preprocess_text(sample_text)
with open('palde_hotel.txt', 'w', encoding='utf-8') as file:  # encoding parametresi eklendi
    file.write(processed_text)
