const elements = {
    conversations: document.getElementById("totalConversations"),
    messages: document.getElementById("totalMessages"),
    unanswered: document.getElementById("totalUnanswered"),
    helpfulRate: document.getElementById("helpfulRate"),
    helpful: document.getElementById("helpfulCount"),
    notHelpful: document.getElementById("notHelpfulCount"),
    questions: document.getElementById("topQuestions"),
    updated: document.getElementById("lastUpdated"),
    refresh: document.getElementById("refreshButton"),
    logout: document.getElementById("logoutButton")
};

let feedbackChart = null;

async function loadDashboard() {
    elements.refresh.disabled = true;
    elements.refresh.textContent = "Loading...";

    try {
        const response = await fetch("/api/admin/stats");
        const data = await response.json();

        if (response.status === 401) {
            window.location.href = "/admin/login";
            return;
        }

        if (!response.ok) {
            throw new Error(data.error || "Unable to load statistics.");
        }

        elements.conversations.textContent = data.total_conversations;
        elements.messages.textContent = data.total_messages;
        elements.unanswered.textContent = data.total_unanswered;
        elements.helpfulRate.textContent = `${data.helpful_rate}%`;

        elements.helpful.textContent = data.feedback.helpful;
        elements.notHelpful.textContent = data.feedback.not_helpful;

        renderFeedbackChart(data.feedback);
        renderTopQuestions(data.top_questions);

        elements.updated.textContent =
            "Last updated: " + new Date().toLocaleTimeString();

    } catch (error) {
        console.error("Dashboard error:", error);
        elements.questions.textContent =
            "Unable to load dashboard data. Please refresh.";
    } finally {
        elements.refresh.disabled = false;
        elements.refresh.textContent = "↻ Refresh data";
    }
}

function renderFeedbackChart(feedback) {
    const canvas = document.getElementById("feedbackChart");

    if (feedbackChart) {
        feedbackChart.destroy();
    }

    feedbackChart = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: ["Helpful", "Not helpful"],
            datasets: [{
                data: [feedback.helpful, feedback.not_helpful],
                backgroundColor: ["#48d6a0", "#8b7cff"],
                borderColor: "#10182b",
                borderWidth: 5,
                hoverOffset: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#cbd5e1",
                        padding: 20
                    }
                }
            }
        }
    });
}

function renderTopQuestions(questions) {
    elements.questions.replaceChildren();

    if (!questions || questions.length === 0) {
        const empty = document.createElement("p");
        empty.className = "empty-state";
        empty.textContent = "No questions recorded yet.";
        elements.questions.appendChild(empty);
        return;
    }

    questions.forEach(item => {
        const row = document.createElement("div");
        row.className = "question-item";

        const question = document.createElement("strong");
        question.textContent = item.question;

        const frequency = document.createElement("span");
        frequency.textContent = `${item.frequency} times`;

        row.append(question, frequency);
        elements.questions.appendChild(row);
    });
}

elements.refresh.addEventListener("click", loadDashboard);

loadDashboard();

async function loadUnansweredQuestions() {
    const container = document.getElementById("unansweredQuestions");
    const totalElement = document.getElementById("unansweredTotal");

    try {
        const response = await fetch("/api/admin/unanswered");
        const data = await response.json();

        if (!response.ok) {
            throw new Error("Unable to load unanswered questions.");
        }

        totalElement.textContent = data.total;
        container.replaceChildren();

        if (data.questions.length === 0) {
            const empty = document.createElement("p");
            empty.className = "empty-state";
            empty.textContent = "No unanswered questions. Great work!";
            container.appendChild(empty);
            return;
        }

        data.questions.forEach(item => {
            const row = document.createElement("div");
            row.className = "question-item";

            const details = document.createElement("div");

            const question = document.createElement("strong");
            question.textContent = item.question;

            const date = document.createElement("small");
            date.textContent = "Received: " + item.created_at;

            const confidence = document.createElement("small");
            confidence.textContent =
                "Confidence: " + (item.confidence * 100).toFixed(1) + "%";

            details.append(question, date, confidence);
            row.appendChild(details);
            container.appendChild(row);
        });

    } catch (error) {
        console.error("Unanswered questions error:", error);
        container.textContent = "Unable to load unanswered questions.";
    }
}


loadUnansweredQuestions();

const faqForm = document.getElementById("faqForm");

if (faqForm) {
    faqForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const message = document.getElementById("faqFormMessage");
        const submitButton = faqForm.querySelector('button[type="submit"]');

        const faq = {
            category: document.getElementById("faqCategory").value.trim(),
            question: document.getElementById("faqQuestion").value.trim(),
            variations: document.getElementById("faqVariations").value
                .split(",").map(item => item.trim()).filter(Boolean),
            answer: document.getElementById("faqAnswer").value.trim(),
            tags: document.getElementById("faqTags").value
                .split(",").map(item => item.trim()).filter(Boolean)
        };

        submitButton.disabled = true;
        submitButton.textContent = "Adding...";

        try {
            const response = await fetch("/api/admin/faqs", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(faq)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to add FAQ.");
            }

            message.textContent = data.message + " Total FAQs: " + data.total_faqs;
            message.style.color = "#48d6a0";
            faqForm.reset();
            await loadFaqs();

        } catch (error) {
            message.textContent = error.message;
            message.style.color = "#ff7777";
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Add FAQ";
        }
    });
}



async function logoutAdmin() {
    if (!window.confirm("Are you sure you want to log out?")) {
        return;
    }

    try {
        const response = await fetch("/admin/logout", {
            method: "POST"
        });

        if (response.redirected || response.ok) {
            window.location.href = "/admin/login";
        } else {
            alert("Unable to log out. Please try again.");
        }
    } catch (error) {
        console.error("Logout error:", error);
        alert("Unable to log out. Please try again.");
    }
}

if (elements.logout) {
    elements.logout.addEventListener("click", logoutAdmin);
}


// Load and display all FAQs
async function loadFaqs() {
    const faqList = document.getElementById("faqList");
    const faqListTotal = document.getElementById("faqListTotal");

    if (!faqList || !faqListTotal) return;

    try {
        const response = await fetch("/api/admin/faqs");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to load FAQs.");
        }

        faqListTotal.textContent = data.total;
        faqList.replaceChildren();

        if (data.faqs.length === 0) {
            const emptyMessage = document.createElement("p");
            emptyMessage.textContent = "No FAQs have been added yet.";
            faqList.appendChild(emptyMessage);
            return;
        }

        data.faqs.forEach(faq => {
            const card = document.createElement("div");
            card.className = "faq-item";

            const category = document.createElement("span");
            category.className = "faq-category";
            category.textContent = faq.category;

            const question = document.createElement("h3");
            question.textContent = faq.question;

            const answer = document.createElement("p");
            answer.textContent = faq.answer;

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "faq-delete-button";
            deleteButton.textContent = "Delete FAQ";
            deleteButton.dataset.faqId = faq.id;

            card.append(category, question, answer, deleteButton);
            faqList.appendChild(card);
        });

    } catch (error) {
        faqList.textContent = error.message;
    }
}


// Delete an FAQ after confirmation
const faqListContainer = document.getElementById("faqList");

if (faqListContainer) {
    faqListContainer.addEventListener("click", async function (event) {
        const button = event.target.closest(".faq-delete-button");

        if (!button) return;

        const faqId = button.dataset.faqId;

        if (!window.confirm("Are you sure you want to delete this FAQ?")) {
            return;
        }

        button.disabled = true;
        button.textContent = "Deleting...";

        try {
            const response = await fetch(`/api/admin/faqs/${faqId}`, {
                method: "DELETE"
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to delete FAQ.");
            }

            await loadFaqs();

        } catch (error) {
            alert(error.message);
            button.disabled = false;
            button.textContent = "Delete FAQ";
        }
    });
}

loadFaqs();
