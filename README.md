# UpTrack - AI-Powered Health & Fitness Tracker

UpTrack is a full-stack health and fitness web application powered by dual AI (Google Gemini + OpenAI) with real-time posture detection, personalized workout/nutrition planning, and comprehensive health tracking. Built with Flask, MongoDB, and a modern Tailwind CSS UI.

## Features

### Core Tracking
- **Activity Tracking**: Log daily steps, distance, duration, and calories burned
- **Workout Management**: Manual workout logging with detailed exercise entries
- **Nutrition Tracking**: Log meals with calories and macronutrients (protein, carbs, fat)
- **Goal Setting**: Set and track fitness goals with deadlines and status monitoring
- **Progress Visualization**: Interactive charts using Plotly.js for steps, calories, and workout trends
- **BMR/TDEE Calculator**: Personalized calorie targets using the Mifflin-St Jeor equation

### AI-Powered Features
- **AI Workout Generator**: Personalized workout plans based on your goals, available time, and equipment (Gemini / OpenAI)
- **AI Meal Planner**: Custom meal plans tailored to dietary preferences and health conditions (Gemini / OpenAI)
- **AI Health Insights**: Intelligent analysis of your logged health data with actionable recommendations
- **AI Chat Assistant**: In-app conversational health and fitness assistant (Gemini / OpenAI)
- **Workout Form Photo Analysis**: Upload or capture a photo of your exercise form and receive real-time AI feedback (Gemini / OpenAI vision)

### Real-Time Posture Detection
- **Browser-based MediaPipe AI**: Live webcam pose detection with skeleton overlay — runs entirely in the browser, no images sent to a server
- **Posture analysis**: Detects shoulder alignment, spine angle, and common postural issues in real time
- **Privacy-first**: Camera feed is processed locally; nothing leaves your device

### Authentication & Security
- **Email Verification**: OTP-based signup verification via Gmail SMTP
- **bcrypt Password Hashing**: Industry-standard hashing, passwords never stored as plain text
- **Secure Sessions**: 7-day persistent sessions with HttpOnly, SameSite cookie configuration
- **Password Recovery**: Secure password reset via email OTP (10-minute expiry)
- **Protected Routes**: Decorator-based authentication guards on all sensitive endpoints

### UI & UX
- **Tailwind CSS**: Responsive, modern UI with a custom color palette
- **Dark Mode**: Full dark/light theme toggle
- **Responsive Design**: Mobile-friendly layout across all pages

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.8+, Flask 3.0 |
| Database | MongoDB (Atlas) |
| Authentication | bcrypt, Flask sessions |
| AI (Primary) | Google Gemini (`gemini-flash-latest`) |
| AI (Secondary) | OpenAI GPT-3.5/4 |
| Posture Detection | MediaPipe Pose (browser-side JS) |
| Frontend | HTML5, Tailwind CSS, JavaScript |
| Visualization | Plotly.js |
| Email | SMTP via Gmail |
| Deployment | Vercel (vercel.json included) |

## Prerequisites

- Python 3.8+
- MongoDB Atlas account (free tier works)
- Gmail account with App Password (for email verification)
- Google Gemini API key **or** OpenAI API key (at least one required for AI features)

## Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd WellnessAI
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Flask
SECRET_KEY=your-super-secret-key-change-in-production

# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/wellnessai_db

# Gmail (for email OTP)
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your-16-char-gmail-app-password

# AI — at least one required
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=sk-your-openai-api-key
```

#### Get a Gmail App Password
1. Go to [Google Account](https://myaccount.google.com/) → Security
2. Enable 2-Step Verification
3. Under 2-Step Verification → **App passwords**
4. Generate a password for "WellnessAI" → copy the 16-character code

#### Get a Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key and copy it

### 5. Set Up MongoDB Atlas

1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Add a database user (username + password)
3. Whitelist your IP (or `0.0.0.0/0` for development)
4. Copy the connection string and update `MONGODB_URI` in `.env`

### 6. Run the Application

```bash
python app.py
```

Visit `http://localhost:8000` in your browser.

## Project Structure

```
WellnessAI/
├── app.py                        # Flask application, all routes & business logic
├── requirements.txt              # Python dependencies
├── vercel.json                   # Vercel deployment config
├── config.json                   # Optional config (env vars take precedence)
├── .env                          # Environment variables (create this, don't commit)
├── .gitignore
└── templates/
    ├── base.html                 # Base layout (Tailwind, dark mode, nav)
    ├── home.html                 # Landing page
    ├── login.html                # Login
    ├── signup.html               # Registration
    ├── verify.html               # Email OTP verification
    ├── dashboard.html            # Main dashboard
    ├── activities.html           # Activity logging
    ├── workouts.html             # Workout logging
    ├── ai_workout_generator.html # AI workout planner
    ├── meals.html                # Meal logging
    ├── ai_meal_planner.html      # AI meal planner
    ├── goals.html                # Goal management
    ├── progress.html             # Progress charts
    ├── posture.html              # Real-time posture detection (MediaPipe)
    ├── profile.html              # User profile & settings
    ├── forgot_password.html      # Password recovery
    └── reset_password.html       # Password reset
```

## Database Collections

| Collection | Indexed On | Key Fields |
|---|---|---|
| `users` | email (unique), phone | name, email, hashed password, profile data |
| `activities` | user_id + date | steps, distance, calories, duration |
| `workouts` | user_id + date | workout_type, duration, exercises, calories |
| `meals` | user_id + date | meal_type, food_items, calories, macros |
| `goals` | user_id + status | goal_type, target, deadline, status |
| `ai_insights` | user_id | AI-generated health insights |
| `meal_plans` | user_id | AI-generated meal plans |

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session secret key |
| `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| `GMAIL_USER` | Recommended | Gmail address for OTP emails |
| `GMAIL_PASSWORD` | Recommended | Gmail 16-char App Password |
| `GEMINI_API_KEY` | One of these | Google Gemini API key |
| `OPENAI_API_KEY` | One of these | OpenAI API key |

## Deployment (Vercel)

A `vercel.json` is included for one-command deployment:

```bash
vercel --prod
```

Set the environment variables in your Vercel project dashboard (Settings → Environment Variables).

## Troubleshooting

**MongoDB not connecting** — Verify `MONGODB_URI`, check your IP is whitelisted, and confirm the cluster is not paused.

**Email OTP not arriving** — Check spam, verify Gmail App Password is 16 characters with no spaces, ensure 2-Step Verification is enabled.

**AI features not working** — Ensure at least one of `GEMINI_API_KEY` or `OPENAI_API_KEY` is set. The app falls back to basic recommendations if neither key is available.

**Posture detection not starting** — Allow camera permissions in your browser. The feature requires HTTPS in production (or localhost for development).

## License

MIT License — open source and free to use.

---

**WellnessAI** — Track smarter. Move better. Live healthier.
