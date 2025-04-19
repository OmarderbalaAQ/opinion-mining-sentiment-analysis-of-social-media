from django.shortcuts import render, redirect
from django.conf import settings
import os
import pandas as pd
import nltk
import string
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import SVC

from .image_model import predict_image_sentiment
from .scraping_model import extract_social_media_data

# Ensure nltk dependencies are downloaded
#nltk.download('stopwords')
#nltk.download('punkt')

# TEXT MODEL SETUP
BASE_DIR = settings.BASE_DIR
TRAIN_CSV_PATH = os.path.join(BASE_DIR, 'sentiment', 'data', 'train.csv')
tweets_df = pd.read_csv(TRAIN_CSV_PATH)[['text', 'sentiment']].dropna()

# Text cleaning function
def textClean(text):
    nopunc = [char.lower() for char in text if char not in string.punctuation]
    nopunc = ''.join(nopunc)
    tokens = word_tokenize(nopunc)
    nohttp = [word for word in tokens if word[0:4] != 'http']
    nostop = [word for word in nohttp if word not in stopwords.words('english')]
    return nostop

vectorizer = CountVectorizer(analyzer=textClean)
message = vectorizer.fit_transform(tweets_df['text'])
svc_model = SVC(C=0.2, kernel='linear', gamma=0.8)
svc_model.fit(message, tweets_df.sentiment)

# Shared prediction function
def analyze_sentiment(texts):
    predictions = vectorizer.transform(texts)
    results = svc_model.predict(predictions)
    emoji_map = {'positive': '😀', 'negative': '😞', 'neutral': '😐'}
    return [(text, sentiment, emoji_map.get(sentiment, '❓')) for text, sentiment in zip(texts, results)]

# TEXT VIEWS
def home(request):
    return render(request, "sentiment/index.html")

def result(request):
    if request.method == "POST":
        text = request.POST.get("text", "")
        if text:
            result = analyze_sentiment([text])[0]
            return render(request, "sentiment/text_result.html", {
                "text": result[0],
                "sentiment": result[1],
                "emoji": result[2]
            })
    return redirect("home")

# URL VIEWS
def url_input(request):
    return render(request, "sentiment/url_input.html")

def url_result(request):
    if request.method == "POST":
        url = request.POST.get("url")
        if url:
            result = extract_social_media_data(url)
            text_sentiment = analyze_sentiment([result["combined_text"]])[0]
            text_label = text_sentiment[1]
            emoji = text_sentiment[2]

            image_sentiment = "No image found"
            image_path = None
            image_folder = os.path.join(settings.BASE_DIR, result["image_folder"])
            images = os.listdir(image_folder)

            if images:
                image_path = os.path.join(result["image_folder"], images[0])
                full_image_path = os.path.join(image_folder, images[0])
                image_sentiment = predict_image_sentiment(full_image_path)

            return render(request, "sentiment/url_result.html", {
                "url": url,
                "text_sentiment": text_label,
                "emoji": emoji,
                "image_sentiment": image_sentiment,
                "image_path": image_path,
                "post_text": result["combined_text"],
            })
    return redirect("url_input")
