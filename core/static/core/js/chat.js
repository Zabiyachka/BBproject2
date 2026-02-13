document.addEventListener("DOMContentLoaded", () => {
    const el = document.getElementById("ai-text");
    if (!el) return;

    const text = el.dataset.text;
    let i = 0;

    function type() {
        if (i < text.length) {
            // ✅ ЗМІНЕНО: Використовуємо innerHTML замість textContent
            // Перевіряємо чи це початок <br> тегу
            if (text.substr(i, 4) === '<br>') {
                el.innerHTML += '<br>';
                i += 4; // Пропускаємо всі 4 символи <br>
            } else {
                el.innerHTML += text.charAt(i);
                i++;
            }
            setTimeout(type, 25); // швидкість друку
        }
    }

    type();
});

// chat.js

async function sendMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    
    if (!message) return;
    
    // Показуємо повідомлення користувача
    addMessageToChat("user", message);
    input.value = "";
    
    try {
        const response = await fetch("/chat/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        // Логуємо контекст (для дебагу)
        console.log("Контекст розмови:", data.context_summary);
        console.log("Релевантність:", data.is_relevant);
        console.log("Впевненість:", data.confidence);
        
        // Показуємо попередження якщо не про баскетбол
        if (!data.is_relevant) {
            addMessageToChat("system", "⚠️ Схоже, це питання не про баскетбол");
        }
        
        // Показуємо контекст (опціонально)
        if (data.context_summary && data.context_summary !== "Нова розмова") {
            console.log("Ми обговорювали:", data.context_summary);
        }
        
        // Показуємо відповідь AI
        addMessageToChat("assistant", data.response);
        
    } catch (error) {
        console.error("Помилка:", error);
        addMessageToChat("system", "Помилка відправки повідомлення");
    }
}

// ✅ ОНОВЛЕНА ФУНКЦІЯ - тепер підтримує HTML
function addMessageToChat(role, text) {
    const chatBox = document.getElementById("chat-box");
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;
    
    // ✅ ЗМІНЕНО: Використовуємо innerHTML для підтримки <br>
    messageDiv.innerHTML = text;
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}