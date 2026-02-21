import os
from dotenv import load_dotenv
from django.shortcuts import render, redirect
from django.http import JsonResponse 
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json  
import logging
from openai import OpenAI
from .models import Todo, ChatMessage
from datetime import date
import html
import re

# Імпорт алгоритмів
from .algorithms import ChatContextManager, ResponseFilter

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Configuration constants
CHAT_MAX_MESSAGES = 10  # Number of messages to keep in context
CHAT_MAX_TOKENS = 3000  # Token limit for context
API_TIMEOUT = 30  # API request timeout in seconds

# Dictionary for storing context
# Stores context managers for each user session
chat_managers = {}


def convert_markdown_to_html(text):
    """Convert markdown-style formatting to HTML."""
    if not text:
        return text
    
    # Escape any HTML first to prevent injection
    text = html.escape(text)
    
    # Convert markdown headers to styled divs
    text = re.sub(r'^### (.+)$', r'<div style="font-size: 18px; font-weight: 700; color: #1f2937; margin: 16px 0 8px 0;">\1</div>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<div style="font-size: 20px; font-weight: 700; color: #1f2937; margin: 20px 0 12px 0;">\1</div>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<div style="font-size: 24px; font-weight: 700; color: #1f2937; margin: 24px 0 16px 0;">\1</div>', text, flags=re.MULTILINE)
    
    # Convert bold (**text**)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: 600; color: #111827;">\1</strong>', text)
    
    # Convert bullet points (- text)
    text = re.sub(r'^- (.+)$', r'<div style="margin-left: 20px; margin-bottom: 8px; display: flex; gap: 8px;"><span style="color: #3b82f6; font-weight: bold;">•</span><span>\1</span></div>', text, flags=re.MULTILINE)
    
    # Add line breaks back (they got escaped)
    text = text.replace('\n', '<br>')
    
    return text



@require_http_methods(["GET", "POST"])
@login_required(login_url='login')
def chat_view(request):
    """Handle basketball coach chat interactions with context management."""
    reply = None
    error = None
    context_info = None
    chat_history = []
    user = request.user

    try:
        if request.method == "POST":
            # Check if it's AJAX (JSON) request
            user_message = None
            is_json_request = request.content_type == 'application/json'
            
            if is_json_request:
                try:
                    data = json.loads(request.body)
                    user_message = data.get("message", "").strip()
                except json.JSONDecodeError:
                    return JsonResponse({"error": "Invalid JSON"}, status=400)
            else:
                # Regular form submission
                user_message = request.POST.get("message", "").strip()

            if user_message:
                user_id = user.id

                # Save user message to database
                ChatMessage.objects.create(user=user, role='user', content=user_message)

                # Create or retrieve context manager for user
                if user_id not in chat_managers:
                    chat_managers[user_id] = ChatContextManager(
                        max_messages=CHAT_MAX_MESSAGES,
                        max_tokens=CHAT_MAX_TOKENS
                    )
                
                context_manager = chat_managers[user_id]

                # Store user message
                context_manager.add_message("user", user_message)

                try:
                    # Get conversation history
                    messages = context_manager.get_context_for_api()
                    logger.info(f"Chat messages for API: {len(messages)} messages")
                    
                    # System prompt
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

                    # Call OpenAI API with full conversation history
                    logger.info(f"Calling OpenAI API with {len(messages)} messages for user {user.username}")
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        timeout=API_TIMEOUT
                    )

                    reply = response.choices[0].message.content
                    logger.info(f"Received response from OpenAI: {reply[:100]}")
                    reply = html.unescape(reply)
                    reply = reply.replace('\\u000A', '\n')
                    
                    # Convert markdown to HTML for better display
                    reply_html = convert_markdown_to_html(reply)
                    
                    # Store HTML formatted reply to database
                    ChatMessage.objects.create(user=user, role='assistant', content=reply_html)
                    logger.info(f"Saved assistant message to database for user {user.username}")
                    
                    # Store AI response in memory for context manager
                    context_manager.add_message("assistant", reply)

                    # Filter response - wrap in try/except in case it fails
                    try:
                        filtered_result = ResponseFilter.filter_response(reply, user_message)
                        context_info = {
                            "summary": context_manager.get_conversation_summary(),
                            "is_relevant": filtered_result["is_relevant"],
                            "confidence": filtered_result["confidence"],
                            "warnings": filtered_result["warnings"]
                        }
                    except Exception as filter_error:
                        logger.warning(f"Filter error (non-blocking): {filter_error}")
                        # Continue without filtering
                    
                    # Set reply to None since it's already in chat_history
                    reply = None

                except (json.JSONDecodeError, AttributeError) as e:
                    error = f"API Error: Invalid response format - {str(e)}"
                    logger.error(f"JSON/Attribute error in chat: {e}", exc_info=True)
                except Exception as e:
                    error = f"API Error: {str(e)}"
                    logger.error(f"Error in chat: {e}", exc_info=True)
        
        # Load chat history from database filtered by user
        chat_history = ChatMessage.objects.filter(user=user).order_by('created_at')
        
    except Exception as e:
        logger.error(f"Unexpected error in chat_view: {e}")
        error = f"Unexpected error: {str(e)}"
    
    return render(
        request,
        "core/chat.html",
        {
            "reply": reply,
            "error": error,
            "context_info": context_info,
            "chat_history": chat_history
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


@require_http_methods(["POST"])
@login_required(login_url='login')
def reset_chat_context(request):
    """Reset conversation context for current user."""
    user = request.user
    user_id = user.id
    # Remove from memory
    if user_id in chat_managers:
        del chat_managers[user_id]
    # Remove from database
    ChatMessage.objects.filter(user=user).delete()
    logger.info(f"Chat context reset for user: {user.username}")
    
    return JsonResponse({"success": True, "message": "Chat history cleared"})


@login_required(login_url='login')
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


@login_required(login_url='login')
def todo_view(request):
    selected_date = request.GET.get("date") or date.today().isoformat()
    user = request.user

    if request.method == "POST":
        title = request.POST.get("title")
        todo_date = request.POST.get("date")

        if title and todo_date:
            Todo.objects.create(user=user, title=title, date=todo_date)

        return redirect(f"/todo/?date={todo_date}")

    todos = Todo.objects.filter(user=user, date=selected_date).order_by("-created_at")

    return render(request, "core/todo.html", {
        "todos": todos,
        "selected_date": selected_date
    })


# ============ AUTHENTICATION VIEWS ============

def register_view(request):
    """User registration view."""
    error = None
    
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        
        # Validation
        if not username or not email or not password1:
            error = "Please fill in all fields"
        elif len(username) < 3:
            error = "Username must be at least 3 characters"
        elif len(password1) < 6:
            error = "Password must be at least 6 characters"
        elif password1 != password2:
            error = "Passwords do not match"
        elif User.objects.filter(username=username).exists():
            error = "Username already exists"
        elif User.objects.filter(email=email).exists():
            error = "Email already exists"
        else:
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            logger.info(f"New user registered: {username}")
            return redirect("home")
    
    return render(request, "core/register.html", {"error": error})


def login_view(request):
    """User login view."""
    error = None
    
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            logger.info(f"User logged in: {username}")
            return redirect("home")
        else:
            error = "Invalid username or password"
    
    return render(request, "core/login.html", {"error": error})


def logout_view(request):
    """User logout view."""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        logger.info(f"User logged out: {username}")
    return redirect("home")