# Quick Start Guide - WellnessAI

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Configuration

**Option A: Using config.json**
Edit `config.json` and add your credentials:
```json
{
  "param": {
    "gmail-user": "your-email@gmail.com",
    "gmail-password": "your-gmail-app-password",
    "openai-api-key": "sk-your-openai-key"
  }
}
```

**Option B: Using Environment Variables**
Create a `.env` file:
```env
SECRET_KEY=your-secret-key
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
OPENAI_API_KEY=sk-your-key
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your-app-password
```

### Step 3: Set Up MongoDB

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Get your connection string
4. Update `MONGODB_URI` in your config

### Step 4: Get Gmail App Password (for email verification)

1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Go to App Passwords
4. Generate a new app password for "Mail"
5. Use this password in your config

### Step 5: Get OpenAI API Key (Optional)

1. Sign up at [OpenAI](https://platform.openai.com/)
2. Get your API key from the dashboard
3. Add it to your config

**Note:** AI features will use fallback recommendations if OpenAI key is not provided.

### Step 6: Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser!

## 🎯 First Steps After Launch

1. **Sign Up**: Create your account
2. **Verify Email**: Check your email for verification code
3. **Complete Profile**: Add your health information
4. **Try AI Features**: 
   - Generate a workout plan
   - Get a meal plan
   - View AI health insights

## 📝 Important Notes

- **OpenAI API**: Optional but recommended for best AI features
- **MongoDB**: Required for data storage
- **Gmail**: Required for email verification
- **Production**: Use environment variables, not config.json

## 🐛 Troubleshooting

**Email not sending?**
- Check Gmail app password is correct
- Ensure 2-Step Verification is enabled
- Check spam folder

**MongoDB connection error?**
- Verify connection string
- Check IP whitelist in MongoDB Atlas
- Ensure database name is correct

**AI features not working?**
- Check OpenAI API key
- Verify you have API credits
- App will use fallback recommendations if API fails

## 🎨 Customization

- Edit `static/css/style.css` to change colors and styling
- Modify templates in `templates/` directory
- Update AI prompts in `app.py` for different recommendations

---

Happy tracking! 🎉
