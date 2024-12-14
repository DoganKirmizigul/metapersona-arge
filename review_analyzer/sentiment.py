from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()
with open("corrected_example.txt", "r", encoding='utf-8') as file:
    text = file.read()
score = analyzer.polarity_scores(text)
print(score)  # {'neg': 0.0, 'neu': 0.353, 'pos': 0.647, 'compound': 0.8316}
