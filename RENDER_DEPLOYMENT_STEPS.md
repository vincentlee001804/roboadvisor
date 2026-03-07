# Render Deployment Steps

## Quick Setup Guide

### Step 1: Prepare Your Firebase Service Account JSON

1. Open `firebase-service-account.json`
2. Copy the **entire JSON content** (all 14 lines)
3. Keep it ready to paste into Render

### Step 2: Deploy on Render

1. **Click "New Web Service →"** on Render dashboard

2. **Connect Repository:**
   - Select your GitHub repository
   - Choose branch: `main`

3. **Basic Settings:**
   - **Name**: `roboadvisor` (or your choice)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you
   - **Branch**: `main`

4. **Build & Start Commands:**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

5. **Add Environment Variables:**
   
   Click "Advanced" → Scroll to "Environment Variables" → Click "Add Environment Variable"
   
   Add these one by one:
   
   | Key | Value |
   |-----|-------|
   | `GEMINI_API_KEY` | Your Gemini API key |
   | `GEMINI_MODEL` | `gemini-3-flash-preview` |
   | `SECRET_KEY` | Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `FIREBASE_SERVICE_ACCOUNT` | **Paste entire JSON from firebase-service-account.json** |
   
   **Important for FIREBASE_SERVICE_ACCOUNT:**
   - Copy the entire JSON content (including all braces and quotes)
   - Paste it as-is into the value field
   - It should look like: `{"type": "service_account", "project_id": "...", ...}`

6. **Click "Create Web Service"**
   - Wait 5-10 minutes for build
   - Check logs for any errors
   - Your app will be live at: `https://roboadvisor.onrender.com`

### Step 3: Verify Deployment

1. Check build logs for errors
2. Visit your live URL
3. Test key features:
   - Dashboard loads
   - Can upload receipt
   - Can view expenses
   - Can set budget

### Troubleshooting

**If build fails:**
- Check logs for missing dependencies
- Verify all environment variables are set
- Make sure `requirements.txt` includes `gunicorn`

**If app crashes:**
- Check runtime logs
- Verify `FIREBASE_SERVICE_ACCOUNT` JSON is valid
- Make sure Firebase project is set up correctly

**If Firebase errors:**
- Verify service account JSON is correct
- Check Firebase Console → Project Settings
- Ensure Firestore and Storage are enabled

### Environment Variables Summary

```
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-3-flash-preview
SECRET_KEY=your_generated_secret_key
FIREBASE_SERVICE_ACCOUNT={"type": "service_account", "project_id": "...", ...}
```

### After Deployment

1. Update README.md with live URL
2. Test all features on live site
3. Add URL to submission form
4. Record demo video if needed

---

**Your app is now live! 🎉**
