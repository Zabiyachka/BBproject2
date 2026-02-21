from django.urls import path
from .views import home, chat_view, calories_view, todo_view, compare_players_view, parse_player_view, reset_chat_context, register_view, login_view, logout_view

urlpatterns = [
    path('', home, name='home'),
    path('chat/', chat_view, name='chat'),
    path('calories/', calories_view, name='calories'),
    path("todo/", todo_view, name="todo"),
    path('compare-players/', compare_players_view, name='compare_players'),
    path('parse-player/', parse_player_view, name='parse_player'),
    path('reset-chat/', reset_chat_context, name='reset_chat'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]