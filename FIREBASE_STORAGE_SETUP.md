# Firebase Storage Setup - Fix 404 Error

## The Problem
You're getting a 404 error: "The specified bucket does not exist" when uploading images.

## The Solution

### Step 1: Enable Firebase Storage

1. **Go to Firebase Console:**
   - Visit: https://console.firebase.google.com/
   - Select your project: `gen-lang-client-0755740323`

2. **Enable Storage:**
   - Click on **"Build"** in the left sidebar
   - Click on **"Storage"**
   - Click **"Get started"** button
   - Choose **"Start in test mode"** (for hackathon/demo)
   - Select a location (choose closest to you, e.g., `asia-southeast1` for Singapore)
   - Click **"Done"**

3. **Verify Storage is Enabled:**
   - You should see "Storage" in the left sidebar
   - The Storage page should show "Files" tab

### Step 2: Verify Your .env File

Make sure your `.env` file has:
```env
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your-secret-key
FIREBASE_PROJECT_ID=gen-lang-client-0755740323
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
```

**About SECRET_KEY:**
- This is **NOT from Firebase** - it's a Flask secret key you generate yourself
- Used for Flask session security (cookies, flash messages, etc.)
- **Generate one using Python:**
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- Or use any random string (at least 32 characters)
- Example: `SECRET_KEY=fe6fff6eb74f70ee9bae8ca0a9bb1d47ce67b58e39ef1e35b82d7268fe6e306e`

**Note:** The `FIREBASE_PROJECT_ID` should match the `project_id` in your `firebase-service-account.json` file.

### Step 3: Restart Your Flask App

After enabling Storage, restart your Flask application:
```bash
python app.py
```

### Step 4: Test Upload

1. Go to http://127.0.0.1:5000/upload
2. Try uploading a receipt image
3. It should now work!

## Troubleshooting

### Still Getting 404 Error?

1. **Check Storage Rules:**
   - Go to Firebase Console → Storage → Rules
   - Make sure rules allow uploads (test mode should allow everything)

2. **Check Bucket Name:**
   - The bucket name should be: `{project_id}.appspot.com`
   - For your project: `gen-lang-client-0755740323.appspot.com`
   - The code now reads this from your service account automatically

3. **Verify Service Account Permissions:**
   - Make sure your service account has Storage Admin permissions
   - Go to Firebase Console → Project Settings → Service Accounts
   - The service account should have "Storage Admin" role

### Alternative: Use Default Bucket

If you're still having issues, the code will now automatically use the project_id from your service account JSON file, so you don't need to set `FIREBASE_PROJECT_ID` in `.env` (but it's still good to have it).

## Quick Checklist

- [ ] Storage enabled in Firebase Console
- [ ] Storage started in test mode
- [ ] `.env` file configured
- [ ] `firebase-service-account.json` in project root
- [ ] Flask app restarted
- [ ] Test upload works

## Need Help?

If you're still having issues:
1. Check the Flask console for error messages
2. Verify Storage is enabled in Firebase Console
3. Make sure the bucket name matches your project ID
