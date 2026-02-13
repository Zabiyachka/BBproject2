import os
from dotenv import load_dotenv
from django.shortcuts import render, redirect
from django.http import JsonResponse 
from django.views.decorators.csrf import csrf_exempt  
import json  
from openai import OpenAI
from .models import Todo
from datetime import date
import html

# Імпорт алгоритмів
from .algorithms import ChatContextManager, ResponseFilter

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Словник для зберігання контексту
# Зберігає менеджери контексту для кожного користувача
chat_managers = {}



@csrf_exempt  
def chat_view(request):
    reply = None
    error = None
    context_info = None

    if request.method == "POST":
        # Перевірка чи це AJAX запит (JSON)
        if request.content_type == 'application/json':
            
            try:
                data = json.loads(request.body)
                user_message = data.get("message")
            except:
                return JsonResponse({"error": "Invalid JSON"}, status=400)
        else:
            # Для звичайної форми
            user_message = request.POST.get("message")

        if not request.session.session_key:
            request.session.create()
        
        user_id = request.session.session_key

        #Створення або отримання менеджера контексту
        if user_id not in chat_managers:
            chat_managers[user_id] = ChatContextManager(
                max_messages=10,  # Зберігає останні 10 повідомлень
                max_tokens=3000   # Ліміт токенів
            )
        
        context_manager = chat_managers[user_id]

        # Зберігаємо повідомлення користувача
        context_manager.add_message("user", user_message)

        try:
            # Отримуємо історію розмови
            messages = context_manager.get_context_for_api()
            
            # Системний промпт на початок
            system_prompt = {
                "role": "system",
                "content": """You are a basketball AI coach and expert.
                Answer questions about:
                - NBA, Euroleague and other leagues
                - Player statistics (PPG, RPG, APG)
                - Game analysis and team strategies
                - Basketball history and rules
                - Training and fitness advice for basketball players
                
                Be helpful, concise, and encouraging."""
            }
            messages.insert(0, system_prompt)

            # Тепер передаємо всю історію
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,  # Замість окремих повідомлень - вся історія!
                timeout=30
            )

            reply = response.choices[0].message.content
            reply = html.unescape(reply)
            reply = reply.replace('\\u000A', '\n')  # Очищаємо Unicode
            reply = reply.replace('\n', '<br>')  

            # Зберігаємо відповідь AI
            context_manager.add_message("assistant", reply)

            # Фільтруємо відповідь
            filtered_result = ResponseFilter.filter_response(reply, user_message)
            reply = filtered_result["filtered"]

            # Інформація про контекст
            context_info = {
                "summary": context_manager.get_conversation_summary(),
                "is_relevant": filtered_result["is_relevant"],
                "confidence": filtered_result["confidence"],
                "warnings": filtered_result["warnings"]
            }

        except Exception as e:
            error = str(e)
            print(f"Error in chat: {e}")  # Для дебагу

    return render(
        request,
        "core/chat.html",
        {
            "reply": reply,
            "error": error,
            "context_info": context_info  #  Передаємо контекст в template
        }
    )


# ДОДАЙ: Нова функція для порівняння гравців
def compare_players_view(request):
    """
    Порівняння двох гравців
    URL: /compare-players/?p1=LeBron&p2=Curry
    """
    from .algorithms import PlayerStats, PlayerComparator
    
    player1_name = request.GET.get('p1', 'Player 1')
    player2_name = request.GET.get('p2', 'Player 2')
    
    # Тимчасові дані 
    player1_data = {
        'name': player1_name,
        'points': 2056,
        'rebounds': 624,
        'assists': 816,
        'games_played': 80
    }
    
    player2_data = {
        'name': player2_name,
        'points': 2400,
        'rebounds': 400,
        'assists': 560,
        'games_played': 80
    }
    
    p1 = PlayerStats(player1_data)
    p2 = PlayerStats(player2_data)
    
    comparison = PlayerComparator.compare_players(p1, p2)
    
    return JsonResponse(comparison)


# Функція для парсингу гравців
def parse_player_view(request):
    """
    Парсить текст з даними гравця
    URL: /parse-player/?text=LeBron James: 25.7 PPG, 7.8 RPG, 10.2 APG
    """
    from .algorithms import DataParser
    
    text = request.GET.get('text', '')
    
    parsed_data = DataParser.parse_player_string(text)
    
    if parsed_data:
        return JsonResponse({
            "success": True,
            "data": parsed_data
        })
    else:
        return JsonResponse({
            "success": False,
            "error": "Не вдалося розпарсити текст"
        })


# Функція для скидання контексту
def reset_chat_context(request):
    """
    Скидає контекст розмови для поточного користувача
    """
    if request.session.session_key:
        user_id = request.session.session_key
        if user_id in chat_managers:
            del chat_managers[user_id]
    
    return JsonResponse({"success": True, "message": "Контекст скинуто"})


def calories_view(request):
    calories = None

    if request.method == "POST":
        gender = request.POST.get("gender")
        age = int(request.POST.get("age"))
        height = int(request.POST.get("height"))
        weight = int(request.POST.get("weight"))
        activity = float(request.POST.get("activity"))

        if gender == "male":
            bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
        else:
            bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)

        calories = round(bmr * activity)

    return render(request, "core/calories.html", {
        "calories": calories
    })


def home(request):
    return render(request, "core/home.html")


def todo_view(request):
    selected_date = request.GET.get("date") or date.today().isoformat()

    if request.method == "POST":
        title = request.POST.get("title")
        todo_date = request.POST.get("date")

        if title and todo_date:
            Todo.objects.create(title=title, date=todo_date)

        return redirect(f"/todo/?date={todo_date}")

    todos = Todo.objects.filter(date=selected_date).order_by("-created_at")

    return render(request, "core/todo.html", {
        "todos": todos,
        "selected_date": selected_date
    })


def calendar_view(request):
    return render(request, "core/calendar.html")