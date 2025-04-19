from django.db import models

class Tweet(models.Model):
    text = models.TextField()
    sentiment = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.text[:50]}... ({self.sentiment})"


