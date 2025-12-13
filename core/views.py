import os
from django.shortcuts import render
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chat_view(request):
    reply = None
    error = None

    if request.method == "POST":
        user_message = request.POST.get("message")

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ти баскетбольний AI тренер. Даєш програми тренувань і факти про гравців."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                timeout=20
            )

            reply = response.choices[0].message.content

        except Exception as e:
            error = str(e)

    return render(request, "core/chat.html", {
        "reply": reply,
        "error": error
    })
