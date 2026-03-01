# Firebase Setup Guide for Flask App

## Quick Setup (15 minutes)

### 1. Create Firebase Project
1. Go to https://console.firebase.google.com/
2. Click "Add project"
3. Name it (e.g., "robo-advisor")
4. Disable Google Analytics (optional for hackathon)
5. Create project

### 2. Enable Services
- **Firestore Database**: Enable in "Build" → "Firestore Database" → Create database (Start in test mode)
- **Storage**: Enable in "Build" → "Storage" → Get started (Start in test mode)

### 3. Get Credentials
1. Go to Project Settings (gear icon)
2. Scroll to "Your apps"
3. Click Web icon (`</>`)
4. Register app (name: "robo-advisor-web")
5. Copy the `firebaseConfig` object

### 4. Install Firebase Admin SDK (for Python/Flask)
```bash
pip install firebase-admin
```

### 5. Download Service Account Key
1. Project Settings → Service Accounts
2. Click "Generate new private key"
3. Save as `firebase-service-account.json` (add to .gitignore!)

## Environment Variables

Add to your `.env`:
```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
```

## Firebase Free Tier Limits
- **Firestore**: 50K reads/day, 20K writes/day, 20K deletes/day
- **Storage**: 5GB storage, 1GB/day downloads
- **More than enough for a hackathon demo!**
