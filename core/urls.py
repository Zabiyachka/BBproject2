from django.urls import path
from .views import home, chat_view, calories_view, todo_view, calendar_view

urlpatterns = [
    path('', home, name='home'),
    path('chat/', chat_view, name='chat'),
    path('calories/', calories_view, name='calories'),
    path("todo/", todo_view, name="todo"),
    path("calendar/", calendar_view, name="calendar"),
]