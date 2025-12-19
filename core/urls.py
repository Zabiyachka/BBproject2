from django.urls import path
from .views import home, chat_view, calories_view

urlpatterns = [
    path('', home, name='home'),
    path('chat/', chat_view, name='chat'),
    path('calories/', calories_view, name='calories'),
]