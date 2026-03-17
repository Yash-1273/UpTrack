# Quick Setup Guide - WellnessAI

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get MongoDB Connection String

**Option A: MongoDB Atlas (Recommended - Free)**
1. Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create free cluster
3. Create database user (save password!)
4. Whitelist IP (0.0.0.0/0 for development)
5. Get connection string: `mongodb+srv://user:pass@cluster.mongodb.net/`

**Option B: Local MongoDB**
```bash
# Install MongoDB locally, then use:
mongodb://localhost:27017/
```

### 3. Create .env File

Create `.env` in project root:

```env
SECRET_KEY=generate-random-key-here
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/wellnessai_db
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your-gmail-app-password
OPENAI_API_KEY=sk-optional-key
```

**Generate Secret Key:**
```python
import secrets
print(secrets.token_hex(32))
```

**Get Gmail App Password:**
1. Google Account → Security → 2-Step Verification → App Passwords
2. Generate password for "Mail"
3. Copy 16-character password

### 4. Run Application

```bash
python app.py
```

Visit: `http://localhost:8000`

## ✅ Verification

You should see:
- ✓ MongoDB connected successfully!
- Server running on port 8000

## 🎯 First Steps

1. **Sign Up**: Create account
2. **Verify Email**: Check inbox for code
3. **Login**: Access dashboard
4. **Start Tracking**: Log activities, workouts, meals

## ❗ Common Issues

**MongoDB not connecting?**
- Check connection string format
- Verify username/password
- Check IP whitelist in Atlas

**Email not sending?**
- Verify Gmail app password (not regular password)
- Check 2-Step Verification is enabled
- Check spam folder

**Sessions not persisting?**
- Verify SECRET_KEY is set
- Check browser allows cookies
- Clear browser cache

## 📚 Full Documentation

See `README.md` for complete setup instructions.
