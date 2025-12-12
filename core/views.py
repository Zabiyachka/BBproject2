from django.shortcuts import render

def home(request):
    return render(request, "core/home.html")




def chat_view(request):
    reply = None  # Ответ бота

    if request.method == "POST":
        user_message = request.POST.get("message")

        # ⚠️ Пока ответ — заглушка
        reply = f"Вы написали: {user_message}"

    return render(request, "core/chat.html", {"reply": reply})
