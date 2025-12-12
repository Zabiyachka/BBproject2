from django.urls import path
from .views import home, chat_view

urlpatterns = [
    path("", home, name="home"),
    path("chat/", chat_view, name="chat"),
]
