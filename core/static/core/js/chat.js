document.addEventListener("DOMContentLoaded", () => {
    const el = document.getElementById("ai-text");
    if (!el) return;

    const text = el.dataset.text;
    let i = 0;

    function type() {
        if (i < text.length) {
            el.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, 25); // швидкість друку
        }
    }

    type();
});
