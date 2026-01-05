import os
from dotenv import load_dotenv
from django.shortcuts import render
from openai import OpenAI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


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
                        "content": "You are a basketball AI coach."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                timeout=30
            )

            reply = response.choices[0].message.content

        except Exception as e:
            error = str(e)

    return render(
        request,
        "core/chat.html",
        {
            "reply": reply,
            "error": error
        }
    )
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
