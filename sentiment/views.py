from django.shortcuts import render, redirect
from django.conf import settings
import os
from urllib.parse import urlparse
from .image_analysis.image_model import predict_image_sentiment
from .text_analysis.text_model import text_analyzer
from sentiment.scrapers.facebook_model import SocialMediaScraper
from sentiment.scrapers.twitter_model import twitter_login, extract_from_tweet, extract_from_hashtag
from .models import TextPrediction, URLPrediction
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, "sentiment/index.html")

def result(request):  
    if request.method == "POST":
        text = request.POST.get("text", "").strip()
        if text:
            try:
                if not hasattr(text_analyzer, 'vectorizer'):
                    raise AttributeError("Text analyzer not ready")
                
                result = text_analyzer.analyze_sentiment(text)[0]
                TextPrediction.objects.create(
                    text=text[:500],
                    sentiment=result[1]
                )
                
                return render(request, "sentiment/text_result.html", {
                    "text": text,
                    "sentiment": result[1],
                    "emoji": result[2]
                })
                
            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                return render(request, "sentiment/text_result.html", {
                    "error": "System error - please try later",
                    "text": text
                })
    return redirect("home")

def url_result(request):  
    if request.method == "POST":
        url = request.POST.get("url", "").strip()
        if not url:
            return redirect("home")

        context = {
            "url": url,
            "text_sentiment": "N/A",
            "emoji": "",
            "image_sentiment": "N/A",
            "image_path": None,
            "post_text": "",
            "error": None
        }

        try:
            platform = urlparse(url).netloc.lower()

            if "facebook" in platform:
                scraper = SocialMediaScraper()
                data = scraper.extract_social_media_data(url)
                if data:
                    return process_social_data(request, data, context, url)

            elif "x.com" in platform or "twitter" in platform:
                twitter_login()
                
                if "/status/" in url:
                    data = extract_from_tweet(url)
                    if data:
                        return process_social_data(request, data, context, url)
                
                elif "/hashtag/" in url or url.startswith("https://x.com/search?q=%23"):
                    limit = min(int(request.POST.get("limit", 3)), 10)
                    data = extract_from_hashtag(url, limit)
                    if data:
                        return process_social_data(request, data, context, url)
                else:
                    context["error"] = "Invalid Twitter URL"
                    return render(request, "sentiment/url_result.html", context)

            else:
                context["error"] = "Unsupported platform"
                return render(request, "sentiment/url_result.html", context)

        except Exception as e:
            logger.error(f"URL analysis failed: {str(e)}")
            context["error"] = "Analysis failed - please try again"
            return render(request, "sentiment/url_result.html", context)

    return redirect("home")

def process_social_data(request, data, context, url):
    post_text = data.get("post_text", "")
    if post_text:
        result = text_analyzer.analyze_sentiment(post_text)[0]
        context.update({
            "text_sentiment": result[1],
            "emoji": result[2],
            "post_text": post_text
        })
    
    image_path = data.get("image_path")
    if image_path:
        context["image_sentiment"] = predict_image_sentiment(image_path)
        context["image_path"] = image_path
    
    URLPrediction.objects.create(
        url=url,
        post_text=post_text,
        text_sentiment=context["text_sentiment"],
        image_sentiment=context["image_sentiment"],
        image_file=image_path
    )
    
    return render(request, "sentiment/url_result.html", context)