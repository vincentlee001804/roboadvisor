# Quick Authentication Setup (2-3 hours)

## Step 1: Enable Firebase Authentication (5 minutes)

1. Go to Firebase Console → Authentication
2. Click "Get started"
3. Enable **Email/Password**
4. Click "Save"

## Step 2: Get Firebase Web Config (2 minutes)

1. Firebase Console → Project Settings → General
2. Scroll to "Your apps" → Click Web icon `</>`
3. Register app (name: "Robo-Advisor")
4. Copy the `firebaseConfig` object

## Step 3: Add Firebase Config to base.html

Add this before `</head>` in `templates/base.html`:

```html
<!-- Firebase SDK -->
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>
<script>
  const firebaseConfig = {
    apiKey: "YOUR_API_KEY_HERE",
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT_ID.appspot.com",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
  };
  firebase.initializeApp(firebaseConfig);
</script>
```

## Step 4: Create Login Template

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
        
        <div id="errorMsg" class="mt-4 text-red-600 text-sm text-center hidden"></div>
    </div>
</div>

<script>
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('errorMsg');
    
    try {
        const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
        const idToken = await userCredential.user.getIdToken();
        
        const response = await fetch('{{ url_for("login") }}', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id_token: idToken})
        });
        
        const data = await response.json();
        if (data.success) {
            window.location.href = '{{ url_for("index") }}';
        } else {
            errorMsg.textContent = 'Login failed: ' + data.error;
            errorMsg.classList.remove('hidden');
        }
    } catch (error) {
        errorMsg.textContent = 'Error: ' + error.message;
        errorMsg.classList.remove('hidden');
    }
});
</script>
{% endblock %}
```

## Step 5: Create Signup Template

Create `templates/signup.html` (same structure, different form handler):

```html
{% extends "base.html" %}

{% block title %}Sign Up - AI Robo-Advisor{% endblock %}

{% block content %}
<div class="max-w-md mx-auto mt-20">
    <div class="soft-card p-8">
        <h2 class="text-2xl font-bold text-gray-800 mb-6 text-center">Sign Up</h2>
        
        <form id="signupForm" class="space-y-4">
            <div>
                <label class="block text-gray-700 font-semibold mb-2">Name</label>
                <input type="text" id="name" required
                       class="w-full border border-gray-300 rounded-lg px-4 py-2">
            </div>
            <div>
                <label class="block text-gray-700 font-semibold mb-2">Email</label>
                <input type="email" id="email" required
                       class="w-full border border-gray-300 rounded-lg px-4 py-2">
            </div>
            <div>
                <label class="block text-gray-700 font-semibold mb-2">Password</label>
                <input type="password" id="password" required minlength="6"
                       class="w-full border border-gray-300 rounded-lg px-4 py-2">
            </div>
            <button type="submit" class="w-full primary-btn">Sign Up</button>
        </form>
        
        <div class="mt-4 text-center">
            <a href="{{ url_for('login') }}" class="text-purple-600 hover:underline">
                Already have an account? Login
            </a>
        </div>
        
        <div id="errorMsg" class="mt-4 text-red-600 text-sm text-center hidden"></div>
    </div>
</div>

<script>
document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorMsg = document.getElementById('errorMsg');
    
    try {
        // Create user in Firebase Auth
        const userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
        const idToken = await userCredential.user.getIdToken();
        
        // Send to backend
        const response = await fetch('{{ url_for("signup") }}', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                id_token: idToken,
                name: name,
                email: email
            })
        });
        
        const data = await response.json();
        if (data.success) {
            window.location.href = '{{ url_for("index") }}';
        } else {
            errorMsg.textContent = 'Signup failed: ' + data.error;
            errorMsg.classList.remove('hidden');
        }
    } catch (error) {
        errorMsg.textContent = 'Error: ' + error.message;
        errorMsg.classList.remove('hidden');
    }
});
</script>
{% endblock %}
```

## Step 6: Add Auth Routes to app.py

Add these routes and decorator:

```python
from functools import wraps
from firebase_admin import auth

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        id_token = request.json.get('id_token')
        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            email = decoded_token['email']
            
            # Store in session
            session['user_id'] = uid
            session['user_email'] = email
            
            # Get or create user in Firestore
            user = firebase.get_user(email=email)
            if not user:
                firebase.create_user(email.split('@')[0], email)
                user = firebase.get_user(email=email)
            
            session['firestore_user_id'] = user['id']
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 401
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        id_token = request.json.get('id_token')
        name = request.json.get('name')
        email = request.json.get('email')
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            
            # Create user in Firestore
            firestore_user_id = firebase.create_user(name, email)
            
            # Store in session
            session['user_id'] = uid
            session['user_email'] = email
            session['firestore_user_id'] = firestore_user_id
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))
```

## Step 7: Update Existing Routes

Replace `firebase.get_first_user()` with:

```python
# At the start of each route function:
if 'firestore_user_id' not in session:
    return redirect(url_for('login'))
user_id = session['firestore_user_id']
user = firebase.get_user(user_id=user_id)
```

## Step 8: Add Logout Button

Add to `templates/base.html` navigation:

```html
{% if session.user_id %}
<a href="{{ url_for('logout') }}" class="text-white hover:text-gray-200">Logout</a>
{% endif %}
```

## Testing

1. Start your app: `python app.py`
2. Go to `/signup` and create an account
3. Login at `/login`
4. All routes should now require authentication

---

**Time Estimate:** 2-3 hours for full implementation

**For Hackathon Demo:** You can keep demo user mode and add auth later if time is tight!
