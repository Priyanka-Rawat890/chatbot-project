import os
import random
from datetime import datetime
import torch
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer

# === Flask setup ===
app = Flask(__name__)
CORS(app)

# === Load AI model ===
print("🤖 Loading DialoGPT-small model... please wait (first time only)")
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")

# Conversation memory (to maintain chat history)
chat_history_ids = None

# === Global personality ===
PERSONALITY = "friendly"  # can be: "friendly", "professional", "sarcastic"


# --- PERSONALITY RESPONSES ---
def style_response(text):
    """Modify tone based on personality."""
    if PERSONALITY == "friendly":
        return text + " 😊" if not text.endswith("!") else text
    elif PERSONALITY == "sarcastic":
        return "😏 " + text
    elif PERSONALITY == "professional":
        return "🤖 " + text
    return text


# --- RULE-BASED RESPONSES ---
def check_rule_based(user_input):
    user_input = user_input.lower()

    if "hello" in user_input or "hi" in user_input or "hey" in user_input:
        return style_response(random.choice([
            "Hello there!", "Hey! How can I assist you today?", "Hi! Nice to meet you!"
        ]))

    elif "bye" in user_input or "goodbye" in user_input:
        return style_response(random.choice([
            "Goodbye! 👋", "See you later!", "Take care!"
        ]))

    elif "thanks" in user_input or "thank you" in user_input:
        return style_response(random.choice([
            "You're welcome!", "No problem!", "Glad I could help!"
        ]))

    elif "time" in user_input:
        return style_response(f"The current time is {datetime.now().strftime('%I:%M %p')}.")

    elif "date" in user_input:
        return style_response(f"Today's date is {datetime.now().strftime('%A, %B %d, %Y')}.")

    elif "joke" in user_input:
        jokes = [
            "Why don’t programmers like nature? It has too many bugs! 🐛",
            "Why did the computer show up late? It had a hard drive!",
            "Why do Java developers wear glasses? Because they don’t C#! 🤓"
        ]
        return style_response(random.choice(jokes))

    elif "clear memory" in user_input or "reset chat" in user_input:
        global chat_history_ids
        chat_history_ids = None
        return style_response("Chat memory has been reset 🧠")

    elif "change personality" in user_input:
        global PERSONALITY
        if "sarcastic" in user_input:
            PERSONALITY = "sarcastic"
        elif "professional" in user_input:
            PERSONALITY = "professional"
        else:
            PERSONALITY = "friendly"
        return style_response(f"Personality changed to {PERSONALITY} mode.")

    return None


# --- AI REPLY GENERATION ---
def generate_ai_reply(user_input):
    global chat_history_ids
    try:
        new_input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors="pt")
        bot_input_ids = torch.cat([chat_history_ids, new_input_ids], dim=-1) if chat_history_ids is not None else new_input_ids

        output_ids = model.generate(
            bot_input_ids,
            max_length=1000,
            pad_token_id=tokenizer.eos_token_id,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

        chat_history_ids = output_ids
        reply = tokenizer.decode(output_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
        return style_response(reply.strip() or "Hmm... I didn’t quite get that.")
    except Exception as e:
        print("⚠️ AI generation error:", e)
        return "Oops! Something went wrong while generating a reply."


# --- Flask API Route ---
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")

    # First, rule-based check
    rule_response = check_rule_based(user_message)
    if rule_response:
        return jsonify({"reply": rule_response})

    # Otherwise use AI
    ai_reply = generate_ai_reply(user_message)
    return jsonify({"reply": ai_reply})


# --- Create modern UI automatically ---
def create_template():
    os.makedirs("templates", exist_ok=True)
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Smart AI Chatbot 🤖</title>
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<style>
body{background:linear-gradient(135deg,#e0f2fe,#f8fafc);}
.chat-card{width:420px;}
.bubble{padding:10px 14px;border-radius:18px;max-width:75%;}
.bubble.user{background:#0ea5e9;color:white;margin-left:auto;}
.bubble.bot{background:#f1f5f9;color:#0f172a;margin-right:auto;}
.typing{width:40px;display:flex;gap:6px;align-items:center;}
.dot{width:8px;height:8px;background:#cbd5e1;border-radius:50%;animation:jump 1s infinite;}
.dot:nth-child(2){animation-delay:.15s}.dot:nth-child(3){animation-delay:.3s}
@keyframes jump{0%,100%{transform:translateY(0);}50%{transform:translateY(-6px);}}
</style>
</head>
<body class="flex items-center justify-center min-h-screen">
<div class="chat-card bg-white rounded-xl shadow-xl overflow-hidden">
  <div class="p-4 bg-gradient-to-r from-blue-600 to-blue-400 text-white flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="bg-white rounded-full w-9 h-9 flex items-center justify-center">🤖</div>
      <div class="font-semibold text-lg">Smart AI Chatbot</div>
    </div>
    <div class="text-sm opacity-80">Hybrid + Personality</div>
  </div>
  <div id="messages" class="p-4 h-96 overflow-auto flex flex-col gap-3 bg-gray-50"></div>
  <div class="p-3 border-t bg-white flex gap-2 items-center">
    <input id="inputMsg" class="flex-1 border rounded-xl p-2 focus:outline-none" placeholder="Type a message...">
    <button id="sendBtn" class="bg-blue-600 text-white px-4 py-2 rounded-xl">Send</button>
  </div>
  <div class="p-2 text-center text-xs text-gray-500">Type “reset chat” to clear memory | “change personality to sarcastic/friendly/professional”</div>
</div>
<script>
const messages=document.getElementById('messages');const input=document.getElementById('inputMsg');const sendBtn=document.getElementById('sendBtn');
function appendBubble(text,who='bot'){const d=document.createElement('div');d.className=(who==='user'?'bubble user':'bubble bot');d.textContent=text;messages.appendChild(d);messages.scrollTop=messages.scrollHeight;}
function showTyping(){const t=document.createElement('div');t.className='typing';t.id='typing';t.innerHTML='<div class="dot"></div><div class="dot"></div><div class="dot"></div>';messages.appendChild(t);}
function hideTyping(){const t=document.getElementById('typing');if(t)t.remove();}
async function sendMessage(){const text=input.value.trim();if(!text)return;appendBubble(text,'user');input.value='';showTyping();
try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});
const data=await r.json();hideTyping();appendBubble(data.reply,'bot');}catch(e){hideTyping();appendBubble('Error contacting server.','bot');}}
sendBtn.addEventListener('click',sendMessage);
input.addEventListener('keypress',e=>{if(e.key==='Enter')sendMessage();});
</script></body></html>"""
    with open("templates/index.html", "w", encoding="utf-8") as f: f.write(html)

create_template()

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    print("\n🚀 Smart Hybrid Chatbot is starting...")
    print("Open http://localhost:5000 in your browser\n")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

