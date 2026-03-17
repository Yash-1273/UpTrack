# Database Setup & Authentication Guide

## 🔐 Authentication System

### How It Works

1. **Password Hashing**
   - Uses bcrypt (industry standard)
   - Passwords never stored in plain text
   - Automatic hash verification on login
   - Legacy password migration supported

2. **Session Management**
   - Server-side sessions
   - 7-day session lifetime
   - Persistent across page refreshes
   - Secure cookie configuration

3. **Email Verification**
   - OTP sent on signup
   - 10-minute expiration
   - Required before login
   - Secure password reset flow

## 🗄️ Database Collections

### Users Collection
```javascript
{
  _id: ObjectId,
  name: String,
  email: String (unique, indexed),
  phone: String (indexed),
  password: String (bcrypt hash),
  dob: Date,
  age: Number,
  gender: String,
  weight: Number,
  height: Number,
  activity_level: String,
  dietary_preferences: Array,
  health_conditions: Array,
  fitness_goals: Array,
  verified: Boolean,
  verified_at: Date,
  created_at: Date,
  last_login: Date,
  otp: String (temporary),
  otp_expires: Date (temporary)
}
```

### Activities Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed with date),
  date: Date (indexed),
  steps: Number,
  distance: Number,
  calories_burned: Number,
  active_minutes: Number,
  activity_type: String,
  notes: String
}
```

### Workouts Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed with date),
  date: Date (indexed),
  workout_type: String,
  duration: Number,
  calories_burned: Number,
  exercises: String,
  notes: String,
  plan: String (for AI-generated)
}
```

### Meals Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed with date),
  date: Date (indexed),
  meal_type: String,
  food_items: String,
  calories: Number,
  protein: Number,
  carbs: Number,
  fats: Number,
  notes: String
}
```

### Goals Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (indexed with status),
  goal_type: String,
  target: String,
  deadline: Date,
  description: String,
  status: String (indexed),
  created_at: Date
}
```

## 📊 Database Indexes

Automatically created on startup:

- `users.email` - Unique index
- `users.phone` - Index for lookups
- `activities(user_id, date)` - Compound index
- `workouts(user_id, date)` - Compound index
- `meals(user_id, date)` - Compound index
- `goals(user_id, status)` - Compound index

## 🔄 Data Persistence

### What Persists
- ✅ User accounts and profiles
- ✅ All activity logs
- ✅ All workout records
- ✅ All meal logs
- ✅ All goals
- ✅ AI-generated plans
- ✅ User sessions (7 days)

### What Doesn't Persist
- ❌ Temporary OTP codes (expire after 10 min)
- ❌ Session data after 7 days of inactivity

## 🛡️ Security Features

1. **Password Security**
   - bcrypt hashing with salt
   - Minimum 6 characters
   - Never logged or displayed

2. **Session Security**
   - HttpOnly cookies
   - Secure flag (in production)
   - SameSite protection
   - Server-side storage

3. **Email Verification**
   - OTP expiration (10 minutes)
   - One-time use codes
   - Secure reset flow

4. **Database Security**
   - Connection string in environment variables
   - No hardcoded credentials
   - Indexed queries for performance

## 🔧 Database Connection

### Connection String Format

**MongoDB Atlas:**
```
mongodb+srv://username:password@cluster.mongodb.net/database_name
```

**Local MongoDB:**
```
mongodb://localhost:27017/database_name
```

### Connection Settings

- `serverSelectionTimeoutMS`: 5000ms
- `connectTimeoutMS`: 5000ms
- `socketTimeoutMS`: 5000ms

### Error Handling

- Graceful fallback to demo mode
- Connection retry on startup
- Clear error messages
- Automatic index creation

## 📝 Testing Database Connection

```python
from pymongo import MongoClient

uri = "your-connection-string"
client = MongoClient(uri)
client.server_info()  # Should print server info
print("✓ Connected successfully!")
```

## 🚨 Troubleshooting Database Issues

### Connection Timeout
- Check network connectivity
- Verify MongoDB URI format
- Check firewall settings
- Verify IP whitelist in Atlas

### Authentication Failed
- Verify username and password
- Check special characters are URL-encoded
- Ensure database user has proper permissions

### Index Creation Errors
- Usually safe to ignore (indexes may already exist)
- Check MongoDB logs for details

### Data Not Saving
- Verify MongoDB is connected (check console)
- Check user is logged in (session exists)
- Verify user_id is correct
- Check MongoDB connection string

## 🔄 Migration Notes

### Password Migration
- Old plain-text passwords automatically upgraded to bcrypt
- Happens on first login after update
- No user action required

### Session Migration
- Old sessions may need re-login
- New sessions use improved security
- 7-day lifetime applies to all sessions

## 📈 Performance Optimization

1. **Indexes**: Automatically created for common queries
2. **Connection Pooling**: Handled by pymongo
3. **Query Optimization**: Uses indexed fields
4. **Data Structure**: Optimized for read/write operations

---

For setup instructions, see `README.md` or `SETUP_GUIDE.md`
