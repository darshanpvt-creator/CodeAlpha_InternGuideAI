# InternGuide AI

**An AI-powered internship and career guidance chatbot for students.**

InternGuide AI helps students find guidance on internships, career preparation, technical skills, projects and interview preparation through an interactive chatbot. It uses Natural Language Processing (NLP) and machine learning-based text similarity to identify relevant answers from a curated FAQ knowledge base.

**Live Application:** https://internguide-ai-tv4u.onrender.com

**GitHub Repository:** https://github.com/darshanpvt-creator/CodeAlpha_InternGuideAI

## Features

- **Intelligent Chatbot:** Understands student questions using NLP and TF-IDF-based similarity matching.
- **Internship Guidance:** Provides answers about internship preparation, applications and career development.
- **Conversation History:** Stores conversations and allows users to retrieve previous messages.
- **User Feedback:** Collects feedback on chatbot responses.
- **Unanswered Question Tracking:** Records questions that need additional knowledge-base coverage.
- **Admin Dashboard:** Provides an overview of chatbot activity and feedback.
- **FAQ Management:** Allows administrators to add, view and remove FAQ entries.
- **Database Integration:** Supports persistent data storage using SQLite locally and PostgreSQL in production.
- **Health Check API:** Provides an endpoint for application health monitoring.

## Technology Stack

| Area | Technologies |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| NLP | NLTK |
| Machine Learning | Scikit-learn, TF-IDF, Cosine Similarity |
| Database | SQLite, PostgreSQL |
| Deployment | Render, Gunicorn |
| Version Control | Git, GitHub |

## Project Structure

```text
InternGuide-AI/
├── chatbot/          # NLP and chatbot logic
├── data/             # FAQ and knowledge-base data
├── database/         # Database-related files
├── static/
│   ├── css/          # Stylesheets
│   └── js/           # Frontend JavaScript
├── templates/        # HTML templates
├── tests/            # Automated tests
├── app.py            # Flask application
├── requirements.txt  # Python dependencies
├── render.yaml       # Render deployment configuration
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/darshanpvt-creator/CodeAlpha_InternGuideAI.git
cd CodeAlpha_InternGuideAI
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file or configure the variables in your deployment environment.

```text
SECRET_KEY=your-secret-key
ADMIN_PASSWORD=your-admin-password
DATABASE_URL=your-database-url
```

Keep credentials private. Never commit `.env` files or expose production secrets.

### 5. Run the application

```bash
python app.py
```

Open the application at:

```text
http://127.0.0.1:5000
```

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Chatbot home page |
| GET | `/api/health` | Application health check |
| POST | `/api/chat` | Send a chatbot message |
| GET | `/api/history/<conversation_id>` | Retrieve conversation history |
| POST | `/api/feedback` | Submit response feedback |
| GET | `/api/conversations` | Retrieve conversations |
| GET | `/admin/login` | Admin login |
| POST | `/admin/logout` | Admin logout |
| GET | `/api/admin/stats` | Retrieve dashboard statistics |
| GET | `/api/admin/unanswered` | View unanswered questions |
| GET/POST | `/api/admin/faqs` | View or add FAQs |
| DELETE | `/api/admin/faqs/<faq_id>` | Remove an FAQ |

## Testing

Run the project test suite:

```bash
python -m pytest tests -q
```

The test suite covers the application's implemented functionality, including chatbot and database operations.

## Deployment

The application is deployed on **Render** using Gunicorn.

The deployment configuration is maintained in `render.yaml`. Production environment variables, including the secret key and administrator password, must be configured securely in the hosting environment.

**Live Demo:** https://internguide-ai-tv4u.onrender.com

## Project Objective

The objective of InternGuide AI is to make internship and career-related guidance more accessible to students through an interactive, NLP-powered chatbot and an administrator-managed knowledge base.

## Author

**DARSHAN G**
B.E. Computer Science and Engineering Student

[LinkedIn](https://www.linkedin.com/in/darshanganesan/) · [GitHub](https://github.com/darshanpvt-creator)

---

*Developed as part of the CodeAlpha Artificial Intelligence Internship.*
