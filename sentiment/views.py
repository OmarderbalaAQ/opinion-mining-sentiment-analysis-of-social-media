from django.shortcuts import render, redirect
from django.conf import settings
from urllib.parse import urlparse
from .image_analysis.image_model import predict_image_sentiment
from .text_analysis.text_model import text_analyzer
from sentiment.scrapers.facebook_model import SocialMediaScraper
from sentiment.scrapers.twitter_model import twitter_login, extract_from_tweet, extract_from_hashtag
from .scrapers.tiktok_model import scrape_tiktok_comments
from .models import TextPrediction, URLPrediction
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, "sentiment/index.html")

def create_url_prediction(url, post_text, text_sentiment, image_sentiment=None, image_confidence=None, image_file=None):
    return URLPrediction.objects.create(
        url=url,
        post_text=post_text,
        text_sentiment=text_sentiment,
        image_sentiment=image_sentiment,
        image_confidence=image_confidence,
        image_file=image_file
    )

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
                logger.error(f"Text analysis failed: {e}")
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
            "image_confidence": "N/A",
            "image_path": None,
            "post_text": "",
            "error": None,
            "comments": [],
            "has_comments": False
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
                    limit = min(int(request.POST.get("limit", 1)), 10)
                    data = extract_from_hashtag(url, limit)
                    if data:
                        combined_text = " ".join([tweet['text'] for tweet in data if 'text' in tweet])
                        if combined_text:
                            result = text_analyzer.analyze_sentiment(combined_text)[0]
                            context.update({
                                "text_sentiment": result[1],
                                "emoji": result[2],
                                "post_text": f"Twitter Hashtag Analysis ({len(data)} tweets)",
                                "comments": [tweet['text'] for tweet in data if 'text' in tweet],
                                "has_comments": True
                            })

                        create_url_prediction(
                            url=url,
                            post_text=context["post_text"],
                            text_sentiment=context["text_sentiment"],
                            image_sentiment=context.get("image_sentiment"),
                            image_confidence=None, 
                            image_file=context.get("image_path")
                        )

                        return render(request, "sentiment/url_result.html", context)
                else:
                    context["error"] = "Invalid Twitter URL. Please provide a link to a tweet or a hashtag."
                    return render(request, "sentiment/url_result.html", context)

            elif "tiktok.com" in platform:
                limit = min(int(request.POST.get("limit", 10)), 20)
                data = scrape_tiktok_comments(url, limit=limit)
                
                confidence = None 

                if data and data.get("comments"):
                    combined_text = " ".join(data["comments"])

                    if combined_text:
                        result = text_analyzer.analyze_sentiment(combined_text)[0]
                        context.update({
                            "text_sentiment": result[1],
                            "emoji": result[2],
                            #"post_text": f"TikTok Video Comments Analysis ({len(data['comments'])} comments)",
                            "post_text": data["comments"],
                            "has_comments": True
                        })

                    if data.get("images"):
                        image_path = data["images"][0]
                        sentiment, confidence = predict_image_sentiment(image_path)
                        context.update({
                            "image_sentiment": sentiment,
                            "image_confidence": f"{confidence:.2f}",
                            "image_path": image_path
                        })
                    
                    create_url_prediction(
                        url=url,
                        post_text=context["post_text"],
                        text_sentiment=context["text_sentiment"],
                        image_sentiment=context.get("image_sentiment"),
                        image_confidence=confidence,
                        image_file=context.get("image_path")
                    )

                    return render(request, "sentiment/url_result.html", context)
                else:
                    context["error"] = "Could not find or process comments for this TikTok video."
                    return render(request, "sentiment/url_result.html", context)

            else:
                context["error"] = "Unsupported platform. Please use a Facebook, Twitter/X, or TikTok URL."
                return render(request, "sentiment/url_result.html", context)

        except Exception as e:
            logger.error(f"URL analysis failed for {url}: {str(e)}")
            context["error"] = "An unexpected error occurred during analysis. Please try again."
            return render(request, "sentiment/url_result.html", context)

    return redirect("home")

def process_social_data(request, data, context, url):
    confidence = None 
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
        sentiment, confidence = predict_image_sentiment(image_path)
        context.update({
            "image_sentiment": sentiment,
            "image_confidence": f"{confidence:.2f}",
            "image_path": image_path
        })

    create_url_prediction(
        url=url,
        post_text=context["post_text"],
        text_sentiment=context["text_sentiment"],
        image_sentiment=context.get("image_sentiment"),
        image_confidence=confidence,
        image_file=image_path
    )

    return render(request, "sentiment/url_result.html", context)
