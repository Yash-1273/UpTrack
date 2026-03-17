# Local Setup Guide - WellnessAI

## Step-by-Step Instructions for Windows

### Prerequisites Check

1. **Python 3.8+** - Check if installed:
   ```powershell
   python --version
   ```
   If not installed, download from [python.org](https://www.python.org/downloads/)

2. **pip** - Usually comes with Python:
   ```powershell
   pip --version
   ```

### Step 1: Install Dependencies

Open PowerShell in the project directory and run:

```powershell
pip install -r requirements.txt
```

**Note:** If you get permission errors, use:
```powershell
pip install -r requirements.txt --user
```

### Step 2: Configure MongoDB

**Option A: Use MongoDB Atlas (Cloud - Recommended)**
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free account
3. Create a new cluster (free tier)
4. Get your connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/`)
5. Add your connection string to `config.json` or set as environment variable

**Option B: Use Local MongoDB**
1. Install MongoDB Community Edition from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Start MongoDB service
3. Use connection string: `mongodb://localhost:27017/`

### Step 3: Configure Email (Optional but Recommended)

For email verification to work:

1. **Gmail Setup:**
   - Go to your Google Account → Security
   - Enable 2-Step Verification
   - Go to App Passwords
   - Generate app password for "Mail"
   - Copy the 16-character password

2. **Update config.json:**
   ```json
   {
     "param": {
       "gmail-user": "your-email@gmail.com",
       "gmail-password": "your-16-char-app-password",
       "openai-api-key": "optional-openai-key"
     }
   }
   ```

### Step 4: Configure OpenAI (Optional)

AI features work without this, but better with it:

1. Sign up at [OpenAI Platform](https://platform.openai.com/)
2. Get API key from dashboard
3. Add to `config.json` or set as environment variable

### Step 5: Run the Application

**Simple way:**
```powershell
python app.py
```

**Alternative (with auto-reload):**
```powershell
flask run --debug
```

The app will start at: **http://localhost:5000**

### Step 6: Access the Application

1. Open your browser
2. Go to: `http://localhost:5000`
3. You should see the WellnessAI homepage!

## Quick Test (Without Full Setup)

If you just want to test the app quickly:

1. **Minimal config.json:**
   ```json
   {
     "param": {
       "gmail-user": "",
       "gmail-password": "",
       "openai-api-key": ""
     }
   }
   ```

2. **Use local MongoDB or MongoDB Atlas connection string**

3. **Run:**
   ```powershell
   python app.py
   ```

**Note:** Email verification won't work without Gmail config, but you can still test other features.

## Troubleshooting

### "Module not found" error
```powershell
pip install -r requirements.txt
```

### "MongoDB connection failed"
- Check your MongoDB connection string
- Ensure MongoDB is running (if local)
- Check network access (if Atlas)

### "Port 5000 already in use"
Change the port in `app.py`:
```python
app.run(debug=True, port=5001)
```

### Email not sending
- Verify Gmail app password is correct
- Check 2-Step Verification is enabled
- Ensure app password is 16 characters (no spaces)

## First Run Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] MongoDB configured (Atlas or local)
- [ ] config.json updated (at least with MongoDB URI)
- [ ] Run `python app.py`
- [ ] Open http://localhost:5000 in browser

## Next Steps After Running

1. **Sign Up** - Create your account
2. **Verify Email** - Check email for code (if configured)
3. **Complete Profile** - Add your health information
4. **Try Features:**
   - Log an activity
   - Generate AI workout
   - Create meal plan
   - Set goals

---

**Need Help?** Check the main README.md for more details!
