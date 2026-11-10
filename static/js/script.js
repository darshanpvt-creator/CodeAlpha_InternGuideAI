const messagesContainer = document.getElementById("messages");
const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");
const newChatButton = document.getElementById("newChatButton");
const suggestionButtons = document.querySelectorAll("[data-question]");
const welcomeSection = document.getElementById("welcomeSection");
const historyList = document.getElementById("historyList");

let conversationId = sessionStorage.getItem("internguide_conversation_id");
let isWaiting = false;

function addMessage(role, content, messageId = null) {
    const message = document.createElement("div");
    message.classList.add("message", role);

    const bubble = document.createElement("div");
    bubble.classList.add("message-bubble");
    bubble.textContent = content;

    message.appendChild(bubble);

    if (role === "assistant" && messageId) {
        const feedback = document.createElement("div");
        feedback.classList.add("feedback-actions");

        const helpfulButton = document.createElement("button");
        helpfulButton.textContent = "Helpful";
        helpfulButton.classList.add("feedback-button");

        const notHelpfulButton = document.createElement("button");
        notHelpfulButton.textContent = "Not Helpful";
        notHelpfulButton.classList.add("feedback-button");

        helpfulButton.addEventListener("click", () => {
            submitFeedback("helpful", messageId, feedback);
        });

        notHelpfulButton.addEventListener("click", () => {
            submitFeedback("not_helpful", messageId, feedback);
        });

        feedback.appendChild(helpfulButton);
        feedback.appendChild(notHelpfulButton);
        message.appendChild(feedback);
    }

    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function submitFeedback(rating, messageId, feedbackContainer) {
    if (!conversationId || !messageId) return;

    const buttons = feedbackContainer.querySelectorAll("button");
    buttons.forEach(button => button.disabled = true);

    try {
        const response = await fetch("/api/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                conversation_id: conversationId,
                message_id: messageId,
                rating: rating
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Feedback could not be saved.");
        }

        feedbackContainer.textContent = "Thank you for your feedback!";

    } catch (error) {
        console.error("Feedback error:", error);
        feedbackContainer.textContent =
            "Unable to save feedback. Please try again.";
    }
}

function showTypingIndicator() {
    const message = document.createElement("div");
    message.id = "typingIndicator";
    message.classList.add("message", "assistant");

    const bubble = document.createElement("div");
    bubble.classList.add("message-bubble", "typing-indicator");
    bubble.textContent = "InternGuide AI is thinking...";

    message.appendChild(bubble);
    messagesContainer.appendChild(message);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById("typingIndicator");
    if (indicator) indicator.remove();
}

async function sendMessage(text) {
    const question = text.trim();

    if (!question || isWaiting) return;

    isWaiting = true;
    sendButton.disabled = true;
    questionInput.disabled = true;

    if (welcomeSection) welcomeSection.style.display = "none";

    addMessage("user", question);
    questionInput.value = "";
    showTypingIndicator();

    try {
        const payload = { question };

        if (conversationId) {
            payload.conversation_id = conversationId;
        }

        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        removeTypingIndicator();

        if (!response.ok) {
            throw new Error(data.error || "Unable to process your question.");
        }

        conversationId = data.conversation_id;

        sessionStorage.setItem(
            "internguide_conversation_id",
            conversationId
        );

        addMessage("assistant", data.answer, data.message_id);
        loadConversationList();

    } catch (error) {
        removeTypingIndicator();
        addMessage(
            "assistant",
            "Sorry, something went wrong. Please try again."
        );
        console.error("Chat error:", error);

    } finally {
        isWaiting = false;
        sendButton.disabled = false;
        questionInput.disabled = false;
        questionInput.focus();
    }
}


async function loadConversationList() {
    if (!historyList) return;

    try {
        const response = await fetch("/api/conversations");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to load conversations.");
        }

        historyList.innerHTML = "";

        if (!data.conversations.length) {
            const emptyMessage = document.createElement("p");
            emptyMessage.className = "history-empty";
            emptyMessage.textContent = "No conversations yet.";
            historyList.appendChild(emptyMessage);
            return;
        }

        data.conversations.forEach(conversation => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "history-item";

            if (conversation.id === conversationId) {
                button.classList.add("active");
            }

            button.title = conversation.title || "Untitled conversation";

            const title = document.createElement("span");
            title.className = "history-title";
            title.textContent = conversation.title || "Untitled conversation";

            const details = document.createElement("small");
            details.textContent = `${conversation.message_count} messages`;

            button.appendChild(title);
            button.appendChild(details);

            button.addEventListener("click", () => {
                loadConversationHistory(conversation.id);
            });

            historyList.appendChild(button);
        });

    } catch (error) {
        console.error("Conversation list error:", error);
        historyList.innerHTML = "";

        const errorMessage = document.createElement("p");
        errorMessage.className = "history-empty";
        errorMessage.textContent = "Unable to load conversations.";
        historyList.appendChild(errorMessage);
    }
}

async function loadConversationHistory(id) {
    try {
        const response = await fetch(
            `/api/history/${encodeURIComponent(id)}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to load conversation.");
        }

        messagesContainer.innerHTML = "";

        if (welcomeSection) welcomeSection.style.display = "none";

        conversationId = id;
        sessionStorage.setItem("internguide_conversation_id", conversationId);

        data.messages.forEach(message => {
            addMessage(message.role, message.content, message.id);
        });

        loadConversationList();

    } catch (error) {
        console.error("History loading error:", error);

        sessionStorage.removeItem("internguide_conversation_id");
        conversationId = null;
        startNewConversation();
    }
}

function startNewConversation() {
    conversationId = null;

    sessionStorage.removeItem("internguide_conversation_id");

    messagesContainer.innerHTML = "";

    if (welcomeSection) welcomeSection.style.display = "";

    loadConversationList();

    questionInput.value = "";
    questionInput.focus();
}

function handleSend() {
    sendMessage(questionInput.value);
}

sendButton.addEventListener("click", handleSend);

questionInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        handleSend();
    }
});

suggestionButtons.forEach(button => {
    button.addEventListener("click", function() {
        sendMessage(button.dataset.question || button.textContent);
    });
});

newChatButton.addEventListener("click", startNewConversation);

if (conversationId) {
    loadConversationHistory(conversationId);
} else {
    startNewConversation();
}

// ===== AUTO SCROLL FIX =====
const chatArea = document.getElementById("chatArea");

function scrollChatToLatest() {
    if (!chatArea) return;

    requestAnimationFrame(() => {
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}

if (messagesContainer && chatArea) {
    const chatObserver = new MutationObserver(() => {
        scrollChatToLatest();
    });

    chatObserver.observe(messagesContainer, {
        childList: true,
        subtree: true,
        characterData: true
    });

    scrollChatToLatest();
}

