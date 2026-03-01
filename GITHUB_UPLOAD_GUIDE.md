# GitHub Upload Guide

## Step-by-Step Instructions

### Step 1: Initialize Git Repository (if not already done)

Open terminal in your MVP folder and run:

```bash
cd "C:\Users\vince\Documents\UTS\BorNEO HackWknd 2026\MVP"
git init
```

### Step 2: Verify .gitignore is Working

Make sure these sensitive files are NOT tracked:
- ✅ `.env` (your API keys)
- ✅ `firebase-service-account.json` (Firebase credentials)
- ✅ `uploads/` (uploaded images)
- ✅ `venv/` (virtual environment)
- ✅ `__pycache__/` (Python cache)

Your `.gitignore` already includes these!

### Step 3: Add All Files

```bash
git add .
```

**Important:** This will add all files EXCEPT those in `.gitignore`

### Step 4: Create Initial Commit

```bash
git commit -m "Initial commit: AI Robo-Advisor for Students - BorNEO HackWknd 2026"
```

### Step 5: Create GitHub Repository

1. Go to https://github.com
2. Click the **"+"** icon in the top right
3. Select **"New repository"**
4. Repository name: `ai-robo-advisor` (or your preferred name)
5. Description: `AI-Powered Robo-Advisor for Students - Financial Literacy Tool`
6. Choose **Public** or **Private**
7. **DO NOT** initialize with README, .gitignore, or license (we already have these)
8. Click **"Create repository"**

### Step 6: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
git remote add origin https://github.com/YOUR_USERNAME/ai-robo-advisor.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

### Step 7: Verify Upload

Go to your GitHub repository page and verify all files are uploaded.

---

## Quick Command Summary

```bash
# Navigate to project folder
cd "C:\Users\vince\Documents\UTS\BorNEO HackWknd 2026\MVP"

# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: AI Robo-Advisor for Students"

# Add remote (replace YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Important Notes

### ✅ Files That WILL Be Uploaded:
- All Python code (`app.py`, `models.py`, services, etc.)
- HTML templates
- `requirements.txt`
- `README.md`
- Documentation files (`.md` files)
- `.gitignore`

### ❌ Files That WON'T Be Uploaded (Protected by .gitignore):
- `.env` - Your API keys and secrets
- `firebase-service-account.json` - Firebase credentials
- `uploads/` - User uploaded images
- `venv/` - Virtual environment
- `__pycache__/` - Python cache files
- `*.db`, `*.sqlite` - Database files

### 🔒 Security Checklist

Before pushing, make sure:
- [ ] `.env` file is NOT in the repository
- [ ] `firebase-service-account.json` is NOT in the repository
- [ ] No API keys are hardcoded in source files
- [ ] `.gitignore` includes all sensitive files

### 📝 For Other Developers

After cloning your repo, they need to:
1. Create `.env` file with their own API keys
2. Download their own `firebase-service-account.json` from Firebase
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python app.py`

---

## Troubleshooting

### "Repository not found" error
- Check your GitHub username and repository name
- Make sure the repository exists on GitHub
- Verify you have write access

### "Authentication failed"
- You may need to use a Personal Access Token instead of password
- Or use GitHub CLI: `gh auth login`

### "Large files" warning
- If you have large files, GitHub may warn you
- Consider using Git LFS for large files
- Or exclude them in `.gitignore`

---

## Next Steps After Upload

1. **Add a License** (optional but recommended)
   - Go to repository → Settings → Add file → Create new file
   - Name it `LICENSE`
   - Choose a license (MIT is common for hackathons)

2. **Add Topics/Tags** (helps discoverability)
   - Go to repository → Click gear icon next to "About"
   - Add topics: `hackathon`, `flask`, `firebase`, `gemini-ai`, `financial-literacy`

3. **Update README** (if needed)
   - Make sure README has clear setup instructions
   - Add screenshots if you have them

4. **Create a Release** (for demo/presentation)
   - Go to repository → Releases → Create a new release
   - Tag: `v1.0.0`
   - Title: "BorNEO HackWknd 2026 - MVP"

---

## Alternative: Using GitHub Desktop

If you prefer a GUI:

1. Download GitHub Desktop: https://desktop.github.com/
2. File → Add Local Repository
3. Select your MVP folder
4. Click "Publish repository"
5. Choose name and visibility
6. Click "Publish repository"

---

You're all set! 🚀
