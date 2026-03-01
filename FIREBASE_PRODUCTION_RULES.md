# Firebase Production Mode Setup

Since you've enabled Firebase Storage and Firestore in **production mode**, you need to configure security rules to allow your app to access them.

## Quick Fix: Switch to Test Mode (Easiest for Hackathon)

If you want the easiest setup for a hackathon demo:

1. **For Firestore:**
   - Go to Firebase Console → Firestore Database → Rules
   - Replace the rules with:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /{document=**} {
         allow read, write: if true;
       }
     }
   }
   ```
   - Click "Publish"

2. **For Storage:**
   - Go to Firebase Console → Storage → Rules
   - Replace the rules with:
   ```javascript
   rules_version = '2';
   service firebase.storage {
     match /b/{bucket}/o {
       match /{allPaths=**} {
         allow read, write: if true;
       }
     }
   }
   ```
   - Click "Publish"

⚠️ **Warning:** These rules allow anyone to read/write. Only use for hackathon demos!

---

## Production Mode Rules (More Secure)

If you want to keep production mode, use these rules that allow authenticated access:

### Firestore Rules (Production Mode)

Go to Firebase Console → Firestore Database → Rules:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Allow read/write for all documents (for hackathon demo)
    // In real production, you'd add user authentication checks
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

### Storage Rules (Production Mode)

Go to Firebase Console → Storage → Rules:

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // Allow read/write for all files (for hackathon demo)
    // In real production, you'd add user authentication checks
    match /{allPaths=**} {
      allow read, write: if true;
    }
  }
}
```

---

## Step-by-Step Instructions

### 1. Set Firestore Rules

1. Go to: https://console.firebase.google.com/
2. Select your project: **Hackathon** (gen-lang-client-0755740323)
3. Click **Firestore Database** in left sidebar
4. Click **Rules** tab
5. Copy and paste the Firestore rules above
6. Click **Publish**

### 2. Set Storage Rules

1. Still in Firebase Console
2. Click **Storage** in left sidebar
3. Click **Rules** tab
4. Copy and paste the Storage rules above
5. Click **Publish**

### 3. Test Your App

After setting the rules:
1. Restart your Flask app
2. Try uploading a receipt
3. It should work now!

---

## Understanding the Rules

### Test Mode vs Production Mode

- **Test Mode:** Allows all reads/writes for 30 days, then locks down
- **Production Mode:** Requires security rules from day 1

### Current Rules Explained

The rules I provided (`allow read, write: if true`) mean:
- ✅ Anyone can read data
- ✅ Anyone can write data
- ⚠️ **Not secure for real production!**
- ✅ **Perfect for hackathon demos**

### For Real Production (After Hackathon)

You'd want rules like:
```javascript
// Firestore - Only allow authenticated users
allow read, write: if request.auth != null;

// Storage - Only allow authenticated users
allow read, write: if request.auth != null;
```

But for now, the open rules are fine for your hackathon demo!

---

## Troubleshooting

### Still Getting Permission Errors?

1. **Check Rules Tab:**
   - Make sure you clicked "Publish" after editing rules
   - Rules take effect immediately after publishing

2. **Check Service Account:**
   - Your service account should have "Firebase Admin" permissions
   - Go to Project Settings → Service Accounts
   - The service account should work with these rules

3. **Verify Collections:**
   - Rules apply to collections: `users`, `expenses`, `budgets`
   - The wildcard `{document=**}` covers all of them

### Common Errors

**Error: "Missing or insufficient permissions"**
- Solution: Make sure rules are published and allow read/write

**Error: "Permission denied"**
- Solution: Check that rules use `if true` (allows everything)

---

## Quick Checklist

- [ ] Firestore Rules set to allow all (if true)
- [ ] Storage Rules set to allow all (if true)
- [ ] Rules published (clicked "Publish" button)
- [ ] Flask app restarted
- [ ] Test upload works

You're all set! 🎉
