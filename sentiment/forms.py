from django import forms
from .models import ImageSentiment, URLSentiment

class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ImageSentiment
        fields = ['image']

class URLInputForm(forms.ModelForm):
    class Meta:
        model = URLSentiment
        fields = ['url']
