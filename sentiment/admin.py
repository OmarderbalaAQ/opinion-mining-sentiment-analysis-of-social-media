from django.contrib import admin
from .models import TextPrediction, URLPrediction

admin.site.register(TextPrediction)
admin.site.register(URLPrediction)
