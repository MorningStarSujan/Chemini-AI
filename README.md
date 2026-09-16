# 🧪 Chemini AI

> **AI-powered Green Chemistry Laboratory Assistant**

Chemini AI is a Flask-based chemistry assistant designed to bring **chemistry knowledge, laboratory safety, green chemistry guidance, chemical information, and experiment support** into a single web application.

The application combines a local chemistry knowledge base and chemical database with the **Google Gemini API**. When a question can be answered from the local knowledge base, Chemini AI can respond without calling Gemini; otherwise, the AI service is used to generate a contextual response.

---

## ✨ Features

### 🤖 AI Assistant — Chemai
- Chemistry question answering powered by Google Gemini.
- Conversation context for follow-up questions.
- Streaming AI responses.
- Local chemical/knowledge matching before an external AI request.
- Response caching to reduce unnecessary API calls.

### 🧪 Chemistry Tools
- Chemical information lookup.
- Chemistry knowledge base.
- Experiment information and details.
- Chemistry calculator.
- Green chemistry guidance.

### 🛡️ Laboratory Safety
- Laboratory safety guidance.
- Safety rules and detailed safety information.
- Chemical hazards, storage, disposal, and greener alternatives in the chemical database.

### 🌱 Green Chemistry
- Green chemistry concepts and guidance.
- Green alternatives associated with supported chemical records.
- Chemical waste-disposal information.

### 📊 History
- Application history for user interactions.
- Admin history view with filtering for **All**, **Responded**, and **Not Responded**.

### 🔐 Admin Console
- Private server-side administrator authentication.
- Passwords stored as secure scrypt hashes.
- CSRF protection for protected admin actions.
- Lightweight protection against repeated login/reset attempts.
- Admin password recovery using a private recovery key.
- AI usage dashboard with locally recorded Gemini request and token statistics.

### 📱 Web App / PWA
- Responsive interface for desktop and mobile screens.
- PWA assets and web manifest included.
- Static application assets and custom UI components.

---

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3 / Flask 3 |
| Frontend | HTML, CSS, JavaScript, Jinja2 |
| AI | Google Gemini API via `google-genai` |
| Configuration | `python-dotenv` |
| Security | Werkzeug password hashing, Flask sessions, CSRF protection |
| Production Server | Gunicorn |
| Data Storage | JSON-based application data and local usage telemetry |

---

## 📁 Project Structure

```text
Chemini-AI/
│
├── app.py                         # Flask application and routes
├── setup_admin.py                 # Local admin provisioning utility
├── requirements.txt               # Python dependencies
├── vercel.json                    # Deployment configuration
├── .env.example                   # Environment variable template
├── .gitignore                     # Git exclusions
│
├── models/
│   ├── ai_engine.py              # Local knowledge + Gemini response engine
│   ├── experiment_manager.py     # Experiment handling
│   ├── recommendation.py         # Recommendation logic
│   └── safety_checker.py         # Safety checks
│
├── utils/
│   ├── gemini_service.py         # Gemini API integration
│   ├── gemini_usage.py           # Local AI usage telemetry
│   ├── ai_identity.py            # AI assistant identity/instructions
│   ├── chat_memory.py            # Conversation context
│   ├── knowledge_base.py         # Local chemistry knowledge
│   ├── chemical_loader.py        # Chemical data loading
│   ├── response_formatter.py     # Structured response formatting
│   ├── calculator.py             # Chemistry calculator utilities
│   ├── cache.py                  # Response caching
│   ├── file_handler.py           # JSON/history handling
│   └── validator.py              # Input validation
│
├── data/
│   ├── chemicals/                # Chemical records by category
│   ├── experiments.json          # Experiment data
│   ├── history.json              # Application history
│   ├── safety_rules.json         # Safety rules
│   └── gemini_usage.json         # Runtime Gemini usage telemetry
│
├── templates/                    # Jinja2 HTML templates
├── static/                       # CSS, JavaScript, images and PWA assets
└── assets/                       # Application branding/assets
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Chemini-AI
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file based on `.env.example`:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.6-flash

SECRET_KEY=

ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=
ADMIN_RESET_TOKEN=

SESSION_COOKIE_SECURE=0
```

> **Never commit your real `.env` file, Gemini API key, admin password hash, or recovery key to Git.**

### 5. Provision the administrator

Run the setup utility from the project directory:

```bash
python setup_admin.py
```

The utility creates/updates the server-side admin credentials and generates a private recovery key.

Save the displayed recovery key securely. It is required for the admin password-reset flow.

After changing the configuration, restart the Flask application.

---

## ▶️ Run Locally

Start the development server with:

```bash
python app.py
```

Then open the local address displayed by Flask, commonly:

```text
http://127.0.0.1:5000
```

The main application, AI Assistant, history, experiments, recommendations, safety tools, calculator, and admin area are served by the Flask application.

---

## 🔑 Admin Access

Chemini AI does **not** provide public administrator registration.

### Admin login

Use the Admin ID and password created by:

```bash
python setup_admin.py
```

### Forgot password

The admin recovery flow uses the private `ADMIN_RESET_TOKEN` generated by the provisioning utility.

The recovery key is a secret credential. Store it outside public source control and do not expose it in the frontend.

### Regenerating credentials

Running `setup_admin.py` again provisions the administrator configuration again and generates a new recovery key. Treat the newly generated key as the current recovery credential.

---

## 🤖 Gemini API & AI Usage

Chemini AI uses the Google Gemini API through the official `google-genai` Python SDK.

The model is configured with:

```env
GEMINI_MODEL=your-model-name
```

The application records local telemetry for Gemini requests made by Chemini AI, including:

- Total requests
- Successful requests
- Failed requests
- Input tokens
- Output tokens
- Total tokens
- Last request time
- Last known API status

This telemetry is stored in:

```text
data/gemini_usage.json
```

### Important: usage vs. remaining quota

The local usage dashboard reports what **this Chemini AI installation has actually sent to Gemini**. It should not be treated as Google's authoritative live remaining quota or billing-credit balance.

For the authoritative Google-side usage, limits, billing, and available credits, use **Google AI Studio / Google Cloud billing and usage information for the project associated with the API key**.

Do not implement a fabricated “credits remaining” value by subtracting local requests from an assumed limit. Gemini limits can vary by model, project, and usage tier.

---

## 🔒 Security Practices

Before deploying Chemini AI publicly:

- Keep `.env` out of Git.
- Never expose `GEMINI_API_KEY` in client-side JavaScript.
- Never expose `ADMIN_PASSWORD_HASH` or `ADMIN_RESET_TOKEN` in HTML/JavaScript.
- Use a strong administrator password.
- Keep the recovery key in a secure password manager or other protected storage.
- Enable `SESSION_COOKIE_SECURE=1` when the application is served over HTTPS.
- Put production deployments behind appropriate HTTPS and infrastructure-level rate limiting.
- Review application logs before exposing the service publicly.

---

## 🌐 Deployment

The repository includes `vercel.json` and a `gunicorn` dependency for deployment workflows.

For production deployment, configure all required environment variables in the hosting provider's **server-side environment settings** rather than committing `.env` to the repository.

At minimum, configure:

```text
GEMINI_API_KEY
GEMINI_MODEL
SECRET_KEY
ADMIN_USERNAME
ADMIN_PASSWORD_HASH
ADMIN_RESET_TOKEN
SESSION_COOKIE_SECURE
```

Use the deployment platform's Python/WSGI configuration according to its current documentation.

---

## 🧪 Chemistry & Safety Disclaimer

Chemini AI is an educational and laboratory-assistance tool. AI-generated information may be incomplete, incorrect, or unsuitable for a specific laboratory environment.

For real laboratory work, always follow your institution's safety procedures, official chemical documentation/SDS, equipment instructions, applicable regulations, and qualified professional supervision. Do not use an AI response as a substitute for required safety documentation or professional judgment.

---

## 🛠️ Development Notes

The application is intentionally structured around a local data layer plus an AI service layer:

1. A user submits a chemistry question.
2. The application normalizes the question.
3. The local knowledge base and chemical database are checked first.
4. If a suitable local response exists, it can be returned without a Gemini request.
5. Otherwise, contextual information and conversation history are passed to Gemini.
6. Gemini's response is streamed or returned to the user.
7. Usage metadata is recorded when supplied by the Gemini SDK.

This architecture helps keep common chemistry information local while reserving external AI calls for questions that need generative assistance.

---

## 📦 Dependencies

Install the pinned dependencies with:

```bash
pip install -r requirements.txt
```

The project currently includes Flask, Google GenAI, Google authentication support, `python-dotenv`, Gunicorn, and the supporting Python packages required by the application.

---

## 🤝 Contributing

Contributions and improvements are welcome.

A typical workflow is:

```bash
git checkout -b feature/your-feature
# Make your changes
git add .
git commit -m "Add your feature"
git push origin feature/your-feature
```

Before opening a pull request, verify that:

- Secrets are not included in the commit.
- The application starts successfully.
- Existing chemistry and safety features continue to work.
- Admin authentication remains protected.
- New AI/API behavior handles errors gracefully.

---

## 📄 License

A `LICENSE` file is present in the repository, but its current contents do not specify a license text. Add your chosen open-source license before publicly distributing the project if licensing terms are required.

---

## 👨‍💻 Project

**Chemini AI** — AI-powered Green Chemistry Laboratory Assistant.

Built to combine chemistry resources, laboratory safety, green chemistry guidance, and generative AI in one practical web application.


## Quota-optimized AI responses
Successful Gemini answers are stored in `data/ai_response_cache.json` for six months. Repeated questions are answered from the local cache without another Gemini request. The cache survives application restarts and Gemini API-key changes.
