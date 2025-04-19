from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page for text input
    path('result/', views.result, name='result'),  # Page to show sentiment result
    path("url/", views.url_input, name="url_input"),
    path("url/result/", views.url_result, name="url_result"),
]