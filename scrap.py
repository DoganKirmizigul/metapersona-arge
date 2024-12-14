import requests
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Proxy listesi
url = 'http://books.toscrape.com/' # Website to make a GET request to
username = 'spw840pgd9'
password = 's462zWieWZtcmZ4~gj'
proxy = f"http://{username}:{password}@gate.smartproxy.com:7000"

# IP'yi kontrol etmek için proxy üzerinden istek gönderiyoruz
ip_check_url = 'https://ip.smartproxy.com/json'
result = requests.get(ip_check_url, proxies={"http": proxy, "https": proxy})  # 'proxies' anahtar kelimesi doğru yazılmalı


# Proxy kullanarak kontrol edilen IP adresini yazdırıyoruz
print(f"IP sorgusu sonucu: {result.text}")


# ChromeDriver ayarları
driver_path = r'C:\Users\Huawei\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe'  # ChromeDriver yolunu doğru girin
service = Service(executable_path=driver_path)

# Kullanılacak User-Agent'lar
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.60",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 OPR/77.0.4054.60",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 10; Mobile; rv:89.0) Gecko/89.0 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 Edg/91.0.864.59",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 OPR/76.0.4017.177",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.77 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; CrOS x86_64 13421.99.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.86 Safari/537.36"
]

# Rastgele bir User-Agent seçiyoruz
user_agent = random.choice(user_agents)
print(f"Kullanılan User-Agent: {user_agent}")

# Tarayıcı ayarlarını yapıyoruz
chrome_options = Options()

# Proxy ayarını tarayıcıya ekliyoruz
chrome_options.add_argument('--proxy-server=http://gate.smartproxy.com:7000')


# User-Agent ayarını ekliyoruz
chrome_options.add_argument(f"user-agent={user_agent}")

# Resimlerin yüklenmesini engelliyoruz
chrome_prefs = {
    "profile.managed_default_content_settings.images": 2  # Resim yüklemeyi devre dışı bırak
}
chrome_options.add_experimental_option("prefs", chrome_prefs)

# Tam ekran modunda başlatıyoruz
chrome_options.add_argument("--start-maximized")

# ChromeDriver'ı başlatıyoruz
driver = webdriver.Chrome(service=service, options=chrome_options)

# Google Maps URL'sine gidiyoruz

driver.get(url)

# Yorumların yüklenmesi için bekleme süresi
time.sleep(5)

# Sayfayı kaydırarak daha fazla yorum yüklenmesini sağlıyoruz
def scroll_down_page(driver, speed=8):
    """Driver'ı kullanarak sayfayı aşağı kaydırır."""
    scroll_pause_time = 10  # Her kaydırma arasında 10 saniye bekleme süresi
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for _ in range(speed):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

scroll_down_page(driver, speed=15)

# "Daha fazla" butonlarına tıklıyoruz
try:
    while True:
        more_buttons = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'w8nwRe')))
        if more_buttons:
            for button in more_buttons:
                driver.execute_script("arguments[0].click();", button)
            time.sleep(2)
        else:
            break
except Exception as e:
    print(f"Daha fazla butonuna tıklarken hata oluştu: {e}")

# Sayfanın HTML kaynağını alıyoruz
page_source = driver.page_source

# BeautifulSoup ile HTML içeriğini parse ediyoruz
soup = BeautifulSoup(page_source, 'html.parser')

# Yorumları saklamak için bir liste oluşturuyoruz
reviews = []

# Yorumları bulmak için HTML sınıfını kullanıyoruz
review_elements = soup.find_all('span', class_='wiI7pd')

# Yorumları listeye ekliyoruz
for element in review_elements:
    review_text = element.text
    reviews.append(review_text)

# Yorumları bir TXT dosyasına yazdırıyoruz
with open('orka_royal_hotel1.txt', 'w', encoding='utf-8') as f:
    for idx, review in enumerate(reviews, 1):
        f.write(f"{idx}. Yorum: {review}\n\n")

print(f"{len(reviews)} yorum 'orka_royal_hotel1.txt' dosyasına yazdırıldı.")

# Tarayıcıyı kapatma
driver.quit()
