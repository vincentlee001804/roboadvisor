# Deployment & Authentication Guide

## 🚀 Hosting Options for Flask App

Since Firebase Hosting only supports static sites, you have two main options:

### Option 1: Render (RECOMMENDED for Hackathon) ⭐

**Why Render?**
- ✅ Free tier available
- ✅ Easy Flask deployment
- ✅ Auto-deploys from GitHub
- ✅ Simple setup (5-10 minutes)
- ✅ Perfect for hackathon demos

**Steps:**

1. **Prepare for Deployment:**
   ```bash
   # Create requirements.txt (if not exists)
   pip freeze > requirements.txt
   
   # Create render.yaml (optional, for easier setup)
   ```

2. **Deploy on Render:**
   - Go to https://render.com
   - Sign up with GitHub
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - **Name**: `roboadvisor` (or your choice)
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python app.py` or `gunicorn app:app`
     - **Environment Variables**: Add all from your `.env` file:
       - `GEMINI_API_KEY`
       - `GEMINI_MODEL`
       - `SECRET_KEY`
       - `FIREBASE_SERVICE_ACCOUNT_PATH`
     - **Add Build Environment Variable**: 
       - Key: `FIREBASE_SERVICE_ACCOUNT`
       - Value: Paste entire JSON content from `firebase-service-account.json`
   - Click "Create Web Service"
   - Wait for deployment (~5 minutes)

3. **Update Firebase Service Account:**
   - In Render dashboard, go to Environment
   - Add `FIREBASE_SERVICE_ACCOUNT` as environment variable
   - Paste the entire JSON content from your `firebase-service-account.json`
   - Update `firebase_service.py` to read from env var if needed

**Alternative: Railway.app** (Similar to Render)
- Go to https://railway.app
- Connect GitHub repo
- Add environment variables
- Deploy!

---

### Option 2: Firebase Cloud Functions (Advanced)

**Note:** This requires restructuring your Flask app. Not recommended for hackathon timeline.

If you want to try:
1. Convert Flask routes to Firebase Functions
2. Use Firebase Hosting for static files
3. More complex but fully Firebase-native

---

## 🔐 Adding Firebase Authentication

### Step 1: Enable Firebase Authentication

1. Go to Firebase Console → Authentication
2. Click "Get started"
3. Enable **Email/Password** provider
4. (Optional) Enable **Google** sign-in for easier demo

### Step 2: Install Firebase Admin SDK (Already installed)

You already have `firebase-admin` installed. Good!

### Step 3: Add Firebase Auth JavaScript SDK to Frontend

Update `templates/base.html` to include Firebase Auth:

```html
<!-- Add before closing </head> tag -->
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>
<script>
  // Initialize Firebase (you'll get this from Firebase Console)
  const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT_ID.appspot.com",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
  };
  firebase.initializeApp(firebaseConfig);
</script>
```

**Get Firebase Config:**
- Firebase Console → Project Settings → General
- Scroll to "Your apps" → Web app → Copy config

### Step 4: Create Authentication Routes

Add to `app.py`:

```python
from firebase_admin import auth

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        # Get ID token from frontend
        id_token = request.json.get('id_token')
        try:
            # Verify the token
            decoded_token = auth.verify_id_token(id_token)
            user_id = decoded_token['uid']
            email = decoded_token['email']
            
            # Store in session
            session['user_id'] = user_id
            session['user_email'] = email
            
            # Get or create user in Firestore
            user = firebase.get_user(email=email)
            if not user:
                # Create user in Firestore
                firebase.create_user(email.split('@')[0], email)
                user = firebase.get_user(email=email)
            
            return jsonify({'success': True, 'user_id': user['id']})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 401
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        # Frontend handles Firebase Auth signup
        # Backend just needs to verify token (same as login)
        return login()  # Reuse login logic
    
    return render_template('signup.html')
```

### Step 5: Create Login/Signup Templates

Create `templates/login.html`:

```html
{% extends "base.html" %}

{% block title %}Login - AI Robo-Advisor{% endblock %}

{% block content %}
<div class="max-w-md mx-auto mt-20">
    <div class="soft-card p-8">
        <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">Login</h2>
        
        <form id="loginForm" class="space-y-4">
            <div>
                <label class="block text-gray-700 font-semibold mb-2">Email</label>
                <input type="email" id="email" required
                       class="w-full border border-gray-300 rounded-lg px-4 py-2">
            </div>
            <div>
                <label class="block text-gray-700 font-semibold mb-2">Password</label>
                <input type="password" id="password" required
                       class="w-full border border-gray-300 rounded-lg px-4 py-2">
            </div>
            <button type="submit" class="w-full primary-btn">Login</button>
        </form>
        
        <div class="mt-4 text-center">
            <a href="{{ url_for('signup') }}" class="text-purple-600 hover:underline">
                Don't have an account? Sign up
            </a>
        </div>
    </div>
</div>

<script>
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        // Sign in with Firebase Auth
        const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
        const idToken = await userCredential.user.getIdToken();
        
        // Send token to backend
        const response = await fetch('{{ url_for("login") }}', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id_token: idToken})
        });
        
        const data = await response.json();
        if (data.success) {
            window.location.href = '{{ url_for("index") }}';
        } else {
            alert('Login failed: ' + data.error);
        }
    } catch (error) {
        alert('Login error: ' + error.message);
    }
});
</script>
{% endblock %}
```

Create `templates/signup.html` (similar structure, use `createUserWithEmailAndPassword`)

### Step 6: Protect Routes

Add authentication check to routes:

```python
def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@require_auth
def index():
    # Get user from session instead of get_first_user()
    user_id = session['user_id']
    user = firebase.get_user(user_id=user_id)
    # ... rest of code
```

### Step 7: Update All Routes

Replace `firebase.get_first_user()` with:
```python
user_id = session['user_id']
user = firebase.get_user(user_id=user_id)
```

---

## 📋 Quick Setup Checklist

### For Hosting (Render):
- [ ] Create Render account
- [ ] Connect GitHub repository
- [ ] Add environment variables
- [ ] Deploy and test
- [ ] Update README with live URL

### For Authentication:
- [ ] Enable Firebase Authentication
- [ ] Add Firebase config to `base.html`
- [ ] Create login/signup templates
- [ ] Add auth routes to `app.py`
- [ ] Add `@require_auth` decorator
- [ ] Update all routes to use session
- [ ] Test login/logout flow

---

## 🎯 Recommended Approach for Hackathon

**For Quick Demo (Recommended):**
1. **Hosting**: Use Render (easiest, ~10 minutes)
2. **Authentication**: 
   - **Option A**: Keep demo user for now, add auth later
   - **Option B**: Add basic Firebase Auth (2-3 hours)

**For Full Production:**
- Complete Firebase Auth implementation
- User sessions
- Protected routes
- Multi-user support

---

## 📝 Environment Variables for Production

Make sure these are set in your hosting platform:

```
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-3-flash-preview
SECRET_KEY=your_secret_key
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
# OR use FIREBASE_SERVICE_ACCOUNT as JSON string
```

---

## 🔗 Useful Links

- Render: https://render.com
- Railway: https://railway.app
- Firebase Auth Docs: https://firebase.google.com/docs/auth
- Firebase Hosting: https://firebase.google.com/docs/hosting

---

## ⚠️ Important Notes

1. **Never commit** `firebase-service-account.json` to GitHub
2. **Always use** environment variables for secrets
3. **Test locally** before deploying
4. **Check** Firebase quotas (free tier is generous)
5. **Update** `.gitignore` to exclude sensitive files

---

Good luck with your submission! 🚀
