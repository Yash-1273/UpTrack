# 🚀 How to Run WellnessAI Locally

## Quick Start (3 Steps)

### ✅ Step 1: Dependencies Installed
All Python packages are already installed! ✓

### ⚙️ Step 2: Configure MongoDB

You need a MongoDB database. Choose one:

**Option A: MongoDB Atlas (Free Cloud - Recommended)**
1. Go to https://www.mongodb.com/cloud/atlas/register
2. Create free account → Create free cluster
3. Click "Connect" → "Connect your application"
4. Copy the connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/`)
5. Update `app.py` line 34 with your connection string, OR set environment variable:
   ```powershell
   $env:MONGODB_URI="mongodb+srv://your-connection-string"
   ```

**Option B: Quick Test (Use existing connection)**
- The app will try to connect to MongoDB Atlas
- If you don't have one, you'll need to set it up first

### 🎯 Step 3: Run the App

Open PowerShell in this directory and run:

```powershell
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

Then open your browser and go to: **http://localhost:5000**

---

## 📝 Configuration Options

### Minimal Setup (Just to test)
You can run with minimal config. The app will work but:
- Email verification won't work (can skip for testing)
- AI features will use fallback recommendations

### Full Setup (Recommended)
1. **MongoDB**: Required for data storage
2. **Gmail**: For email verification (optional but recommended)
3. **OpenAI**: For better AI features (optional)

---

## 🔧 Quick Configuration

### Update MongoDB Connection

**Method 1: Environment Variable (Recommended)**
```powershell
$env:MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
python app.py
```

**Method 2: Edit app.py**
Find line 34 and update:
```python
MONGODB_URI = os.environ.get('MONGODB_URI', 'your-mongodb-connection-string-here')
```

### Update Email (Optional)
Edit `config.json`:
```json
{
  "param": {
    "gmail-user": "your-email@gmail.com",
    "gmail-password": "your-app-password",
    "openai-api-key": "optional"
  }
}
```

---

## 🎉 You're Ready!

Once you run `python app.py`, the app will be available at:
- **URL**: http://localhost:5000
- **Homepage**: You'll see the WellnessAI landing page

### First Steps:
1. Click "Sign Up" to create account
2. Complete your profile
3. Try the AI features!

---

## ❗ Troubleshooting

**"MongoDB connection failed"**
- Make sure you have a valid MongoDB connection string
- Check if MongoDB Atlas cluster is running
- Verify your IP is whitelisted in MongoDB Atlas

**"Port 5000 already in use"**
- Change port in `app.py` last line: `app.run(debug=True, port=5001)`

**Email not working?**
- That's okay! You can still use the app
- Email verification is optional for testing

---

**Need help?** Check `LOCAL_SETUP.md` for detailed instructions!
