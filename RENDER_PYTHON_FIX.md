# Fix Python Version in Render

## Issue
Render is using Python 3.14.3 by default, which causes compatibility issues with protobuf and firebase-admin.

## Solution

### Option 1: Set Python Version in Render Dashboard (Recommended)

1. Go to your Render service dashboard
2. Click on **Settings** tab
3. Scroll to **Environment** section
4. Find **Python Version** setting
5. Set it to: `3.11.9`
6. Click **Save Changes**
7. Trigger a manual redeploy

### Option 2: Use runtime.txt (Already Added)

The `runtime.txt` file is already in your repo with `python-3.11.9`. Render should detect it automatically, but sometimes you need to:

1. Make sure `runtime.txt` is in the root directory (it is)
2. Delete and recreate the service on Render
3. Or manually set Python version in dashboard (Option 1)

### Option 3: Update Dependencies (Already Done)

Updated `requirements.txt` to include:
- `protobuf>=4.25.0` (for Python 3.14 compatibility)
- `firebase-admin>=6.5.0` (newer version)

## Quick Fix Steps:

1. **In Render Dashboard:**
   - Go to your service → Settings
   - Set Python Version to `3.11.9`
   - Save and redeploy

2. **Or recreate service:**
   - Delete current service
   - Create new Web Service
   - Connect same repo
   - Render should detect `runtime.txt` automatically

## Verify:

After redeploy, check build logs:
- Should see: "Installing Python version 3.11.9..."
- NOT: "Installing Python version 3.14.3..."

---

**The easiest fix is Option 1 - just set Python version in Render dashboard!**
