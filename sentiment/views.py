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
from urllib.parse import urlparse
from sentiment.facebook_model import SocialMediaScraper
from sentiment.twitter_model import twitter_login, extract_from_tweet, extract_from_hashtag
from .models import TextPrediction
from .models import URLPrediction

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

def analyze_sentiment(text, image_path=None):
    # Handle empty or invalid input
    if not text or not isinstance(text, str):
        return [(text, "Neutral", "😐")]
    # Wrap single string in a list for vectorizer
    texts = [text] if isinstance(text, str) else text
    predictions = vectorizer.transform(texts)
    results = svc_model.predict(predictions)
    emoji_map = {'positive': '😀', 'negative': '😞', 'neutral': '😐'}
    return [(t, sentiment, emoji_map.get(sentiment.lower(), '❓')) for t, sentiment in zip(texts, results)]

# TEXT VIEWS
def home(request):
    return render(request, "sentiment/index.html")

def result(request):
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            result = analyze_sentiment(text)[0]  # Take first tuple since we passed a single text
            TextPrediction.objects.create(
                text=text,
                sentiment=result[1]
            )
            return render(request, "sentiment/text_result.html", {
                "text": result[0],
                "sentiment": result[1],
                "emoji": result[2]
            })
    return redirect("home")

def url_result(request):
    if request.method == "POST":
        url = request.POST.get("url", "").strip()
        text_sentiment = "N/A"
        emoji = ""
        image_sentiment = "N/A"
        image_path = None
        post_text = ""

        if url:
            platform = urlparse(url).netloc.lower()

            if "facebook" in platform:
                scraper = SocialMediaScraper()
                data = scraper.extract_social_media_data(url)
                if data:
                    post_text = data.get("post_text", "")
                    result = analyze_sentiment(post_text)[0]  # Take first tuple
                    text_sentiment = result[1]
                    emoji = result[2]
                    image_path = data.get("image_path")
                    if image_path:
                        image_sentiment = predict_image_sentiment(image_path)

            elif "x.com" in platform or "twitter" in platform:
                twitter_login()
                if "/status/" in url:
                    data = extract_from_tweet(url)
                    if data:
                        post_text = data.get("post_text", "")
                        result = analyze_sentiment(post_text)[0]  # Take first tuple
                        text_sentiment = result[1]
                        emoji = result[2]
                        image_path = data.get("image_path")
                        if image_path:
                            image_sentiment = predict_image_sentiment(image_path)
                elif "/hashtag/" in url or url.startswith("https://x.com/search?q=%23"):
                    limit = min(int(request.POST.get("limit", 3)), 10)
                    data = extract_from_hashtag(url, limit)
                    if data:
                        post_text = data.get("post_text", "")
                        result = analyze_sentiment(post_text)[0]  # Take first tuple
                        text_sentiment = result[1]
                        emoji = result[2]
                        image_path = data.get("image_path")
                        if image_path:
                            image_sentiment = predict_image_sentiment(image_path)
                else:
                    return render(request, "sentiment/url_result.html", {
                        "url": url,
                        "text_sentiment": "N/A",
                        "emoji": "",
                        "image_sentiment": "N/A",
                        "image_path": None,
                        "post_text": "",
                        "error": "Invalid Twitter URL"
                    })

            else:
                return render(request, "sentiment/url_result.html", {
                    "url": url,
                    "text_sentiment": "N/A",
                    "emoji": "",
                    "image_sentiment": "N/A",
                    "image_path": None,
                    "post_text": "",
                    "error": "Unsupported platform"
                })

            # Save URL prediction
            URLPrediction.objects.create(
                url=url,
                text_sentiment=text_sentiment,
                image_sentiment=image_sentiment
            )

            return render(request, "sentiment/url_result.html", {
                "url": url,
                "text_sentiment": text_sentiment,
                "emoji": emoji,
                "image_sentiment": image_sentiment,
                "image_path": image_path,
                "post_text": post_text
            })

    return redirect("home")