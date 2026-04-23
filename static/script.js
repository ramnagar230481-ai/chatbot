const chatMessages = document.getElementById("chat-messages");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const clearBtn = document.getElementById("clear-btn");
const charCounter = document.getElementById("char-counter");

const MAX_LENGTH = parseInt(userInput.getAttribute("maxlength") || "500", 10);

function formatErrorDetail(detail) {
  if (!detail) {
    return "Something went wrong. Please try again.";
  }
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    const first = detail[0];
    if (first && typeof first === "object" && first.msg) {
      return first.msg;
    }
    return "Request validation failed. Please check your message and try again.";
  }
  if (typeof detail === "object" && detail.error) {
    return detail.error;
  }
  return "Something went wrong. Please try again.";
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addMessage(content, sender) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${sender}-message`;

  if (sender === "bot") {
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = "🤖";
    messageDiv.appendChild(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = `message-bubble ${sender}-bubble`;

  const paragraph = document.createElement("p");
  paragraph.textContent = content;
  bubble.appendChild(paragraph);
  messageDiv.appendChild(bubble);

  chatMessages.appendChild(messageDiv);
  scrollToBottom();
  return messageDiv;
}

function addErrorMessage(content) {
  const messageElement = addMessage(content, "bot");
  messageElement.classList.add("error-message");
  return messageElement;
}

function showTypingIndicator() {
  const messageDiv = document.createElement("div");
  messageDiv.className = "message bot-message";

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "🤖";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble bot-bubble";

  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  for (let i = 0; i < 3; i += 1) {
    const dot = document.createElement("span");
    dot.className = "dot";
    indicator.appendChild(dot);
  }

  bubble.appendChild(indicator);
  messageDiv.appendChild(avatar);
  messageDiv.appendChild(bubble);
  chatMessages.appendChild(messageDiv);
  scrollToBottom();
  return messageDiv;
}

function removeTypingIndicator(element) {
  if (element && element.parentNode) {
    element.parentNode.removeChild(element);
  }
}

async function sendMessage() {
  const userMessage = userInput.value.trim();
  if (!userMessage) {
    return;
  }

  sendBtn.disabled = true;
  userInput.value = "";
  charCounter.textContent = `0/${MAX_LENGTH}`;
  charCounter.classList.remove("warning");

  addMessage(userMessage, "user");
  const typingElement = showTypingIndicator();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMessage }),
    });

    const data = await response.json();
    removeTypingIndicator(typingElement);

    if (response.ok && data.status === "success") {
      addMessage(data.response, "bot");
    } else {
      addErrorMessage(formatErrorDetail(data.detail));
    }
  } catch (error) {
    console.error("Chat request failed:", error);
    removeTypingIndicator(typingElement);
    addErrorMessage("Connection error. Please check your internet and try again.");
  } finally {
    sendBtn.disabled = false;
    userInput.focus();
  }
}

async function clearChat() {
  try {
    const response = await fetch("/clear", { method: "POST" });
    if (!response.ok) {
      throw new Error("Failed to clear chat on server.");
    }
    chatMessages.innerHTML = "";
    addMessage("Hello! I'm an AI chatbot. How can I help you today?", "bot");
  } catch (error) {
    console.error("Clear chat failed:", error);
    addErrorMessage("Failed to clear chat.");
  }
}

document.getElementById("chat-form").addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage();
});

sendBtn.addEventListener("click", (event) => {
  event.preventDefault();
  sendMessage();
});


clearBtn.addEventListener("click", () => {
  clearChat();
});

userInput.addEventListener("input", () => {
  const length = userInput.value.length;
  charCounter.textContent = `${length}/${MAX_LENGTH}`;
  charCounter.classList.toggle("warning", length > MAX_LENGTH * 0.9);
  sendBtn.disabled = length > MAX_LENGTH;
});

window.addEventListener("load", () => {
  userInput.focus();
});
