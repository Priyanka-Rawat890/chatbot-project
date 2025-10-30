// main.js — Frontend logic for AI Chatbot

document.addEventListener("DOMContentLoaded", () => {
  const chatBox = document.getElementById("chat-box");
  const userInput = document.getElementById("user-input");
  const sendBtn = document.getElementById("send-btn");
  const typingIndicator = document.getElementById("typing");

  // Add message to chat box
  function appendMessage(sender, message) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);
    msgDiv.innerHTML = `<strong>${sender === "user" ? "You" : "Bot"}:</strong> ${message}`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // auto-scroll
  }

  // Handle sending user message
  async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage("user", message);
    userInput.value = "";

    typingIndicator.classList.remove("hidden"); // show "typing..."
    
    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = await response.json();
      typingIndicator.classList.add("hidden");

      if (data.response) {
        appendMessage("bot", data.response);
      } else {
        appendMessage("bot", "Sorry, I didn’t understand that.");
      }
    } catch (error) {
      typingIndicator.classList.add("hidden");
      appendMessage("bot", "⚠️ Error connecting to the server.");
      console.error("Error:", error);
    }
  }

  // Event listeners
  sendBtn.addEventListener("click", sendMessage);
  userInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
  });
});
