from django.db import models

class TextPrediction(models.Model):
    text = models.TextField()
    sentiment = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sentiment}: {self.text[:30]}"


class URLPrediction(models.Model):
    url = models.URLField()
    post_text = models.TextField()
    text_sentiment = models.CharField(max_length=10)
    image_sentiment = models.CharField(max_length=10, blank=True, null=True)
    image_file = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.url} [{self.text_sentiment} / {self.image_sentiment}]"
