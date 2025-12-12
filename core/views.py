import requests
from django.shortcuts import render

def home(request):
    return render(request, "core/home.html")




import requests
from django.shortcuts import render

def chat_view(request):
    reply = None
    debug = None

    if request.method == "POST":
        user_message = request.POST.get("message")

        response = requests.post(
            "https://zabiyachka.app.n8n.cloud/webhook/chatbot",
            json={"message": user_message},
            timeout=30
        )

        debug = response.text  # 👈 ВАЖЛИВО
        data = response.json()
        reply = data.get("answer")

    return render(request, "core/chat.html", {
        "reply": reply,
        "debug": debug
    })
