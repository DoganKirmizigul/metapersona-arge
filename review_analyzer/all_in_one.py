import os
import re
from deep_translator import GoogleTranslator
from spellchecker import SpellChecker
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Function to split text into 5000 character chunks
def split_text(text, max_length=5000):
    chunks = []
    while len(text) > max_length:
        split_at = text.rfind(' ', 0, max_length)
        if split_at == -1:
            split_at = max_length
        chunks.append(text[:split_at])
        text = text[split_at:]
    chunks.append(text)
    return chunks

# Function to clean special characters from text
def clean_text(text):
    cleaned_text = re.sub(r'[^\w\s,.!?]', '', text)
    return cleaned_text

# Directory containing the comments
comments_dir = 'api_call/comments1'

# Initialize SpellChecker for English
spell = SpellChecker()

# Loop through each file in the directory
for filename in os.listdir(comments_dir):
    if filename.endswith('.txt'):
        # Open and read the file
        with open(os.path.join(comments_dir, filename), 'r', encoding='utf-8') as file:
            turkish_txt = file.read()

        # Clean the text
        cleaned_turkish_txt = clean_text(turkish_txt)

        # Split the text into chunks
        chunks = split_text(cleaned_turkish_txt)

        # Translate and concatenate the chunks sequentially
        translated_text = ''
        translator = GoogleTranslator(source='tr', target='en')
        for chunk in chunks:
            try:
                translated_text += translator.translate(chunk)
            except Exception as e:
                print(f"Error: {e} - Chunk cannot be translated: {chunk}")

        # Write the translated text to a file
        translated_filename = f"translated_{filename}"
        with open(translated_filename, 'w', encoding='utf-8') as output_file:
            output_file.write(translated_text)

        print(f"Translated text has been saved to '{translated_filename}'")

        # Correct misspelled words in the translated file
        def correct_file(input_path, output_path):
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            total_words = len(content.split())
            corrected_content = []
            for i, word in enumerate(content.split()):
                corrected_word = spell.correction(word)
                corrected_content.append(corrected_word)
                print(f"Process completed: {i+1}/{total_words}")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(' '.join(filter(None, corrected_content)))

            print(f"Corrected file saved as: {output_path}")

        corrected_filename = f"corrected_{translated_filename}"
        correct_file(translated_filename, corrected_filename)

        # Function to collect sentences and analyze sentiment
        def extract_sentences_and_analyze_sentiment(input_filename, keyword):
            with open(input_filename, 'r', encoding='utf-8') as file:
                text = file.read()

            sentences = re.split(r'[.!?]\s*', text)
            relevant_sentences = [sentence for sentence in sentences if keyword in sentence.lower()]

            filtered_text = " ".join(relevant_sentences)
            analyzer = SentimentIntensityAnalyzer()
            sentiment_scores = analyzer.polarity_scores(filtered_text)

            return relevant_sentences, sentiment_scores

        # Analyze sentiment for the entire text
        def analyze_full_text_sentiment(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                text = file.read()

            analyzer = SentimentIntensityAnalyzer()
            sentiment_scores = analyzer.polarity_scores(text)

            return sentiment_scores

        # Perform sentiment analysis for the full text
        full_text_sentiment_scores = analyze_full_text_sentiment(corrected_filename)
        print("Full text sentiment scores:", full_text_sentiment_scores)  # Check sentiment scores

        # Define the output file path
        hotel_name = filename.replace('.txt', '')
        output_sentiment_file = os.path.join('../final_comments/sentiment_analyzed', f"sentiment_scores_{hotel_name}.txt")
        print(f"Saving sentiment scores to {output_sentiment_file}")

        # Check if the directory exists, if not, create it
        output_dir = os.path.dirname(output_sentiment_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Step 1: Check if the file exists and handle accordingly
        if not os.path.exists(output_sentiment_file):
            with open(output_sentiment_file, 'w', encoding='utf-8') as f:
                f.write(f"Sentiment Scores for the entire text ({hotel_name}):\n")
                f.write(str(full_text_sentiment_scores))
            print(f"File did not exist. Created file and wrote sentiment scores for the entire text to: {output_sentiment_file}")
        else:
            with open(output_sentiment_file, 'r+', encoding='utf-8') as f:
                existing_content = f.read()
                if f"Sentiment Scores for the entire text ({hotel_name}):" not in existing_content:
                    f.seek(0, os.SEEK_END)  # Move to the end of the file
                    f.write(f"\nSentiment Scores for the entire text ({hotel_name}):\n")
                    f.write(str(full_text_sentiment_scores))
                    print(f"Full text sentiment scores added.")
                else:
                    print(f"Full text sentiment scores already exist. No changes made.")

        # Step 2: Iterate through each keyword and append sentiment analysis if not already in the file
        keywords = ['bed', 'family', 'food']
        for keyword in keywords:
            relevant_sentences, sentiment_scores_for_keyword = extract_sentences_and_analyze_sentiment(corrected_filename, keyword)
            print(f"Keyword: {keyword}, Sentiment Scores:", sentiment_scores_for_keyword)  # Check keyword sentiment scores

            with open(output_sentiment_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()

            if f"Sentiment Scores for the experience ({keyword}):" not in existing_content:
                with open(output_sentiment_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n\nSentiment Scores for the experience ({keyword}):\n")
                    f.write(str(sentiment_scores_for_keyword))
                print(f"New sentiment scores for keyword '{keyword}' appended to: {output_sentiment_file}")
            else:
                print(f"Keyword '{keyword}' is already logged in the file. No changes made.")
