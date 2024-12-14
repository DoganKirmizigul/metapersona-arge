from spellchecker import SpellChecker

# İngilizce için SpellChecker'ı başlatıyoruz
spell = SpellChecker()

# Dosya yollarını belirtin
input_file = 'palde_hotel.txt'  # Girdi dosyası
output_file = 'corrected_example.txt'  # Çıktı dosyası

# Yanlış yazılan kelimeleri düzelten fonksiyon
def correct_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    corrected_content = []
    for word in content.split():
        # Her kelimeyi kontrol edip düzeltiyoruz
        corrected_word = spell.correction(word)
        corrected_content.append(corrected_word)

    # Düzeltilmiş içeriği yeni dosyaya kaydediyoruz
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(' '.join(filter(None, corrected_content)))  # None değerlerini filtrele

    print(f"Corrected file saved as: {output_path}")

# Programı çalıştırıyoruz
correct_file(input_file, output_file)
