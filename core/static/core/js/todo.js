const form = document.getElementById("todo-form");
const input = document.getElementById("todo-input");
const list = document.getElementById("todo-list");

form.addEventListener("submit", e => {
  e.preventDefault();
  const text = input.value;
  input.value = "";

  const li = document.createElement("li");
  li.textContent = text;
  list.appendChild(li);
});
