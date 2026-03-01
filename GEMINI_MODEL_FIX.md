# Fix: Gemini Model 404 Error

## The Problem
Error: `404 models/gemini-1.5-flash is not found for API version v1beta`

This means the model name `gemini-1.5-flash` is not available with your current API version or region.

## The Solution

### Option 1: Use `gemini-3-flash-preview` (Recommended - Works Well)

Update your `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3-flash-preview
SECRET_KEY=your-secret-key
FIREBASE_PROJECT_ID=gen-lang-client-0755740323
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
```

**Note:** If you don't set `GEMINI_MODEL`, it will default to `gemini-3-flash-preview` automatically.

### Option 2: Try Other Model Names

If `gemini-3-flash-preview` doesn't work, try these in your `.env`:
- `GEMINI_MODEL=gemini-pro` (most compatible)
- `GEMINI_MODEL=gemini-1.5-pro`
- `GEMINI_MODEL=gemini-1.5-flash`
- `GEMINI_MODEL=gemini-2.0-flash-exp` (experimental)

### Option 3: Update the Library

The code now has automatic fallback logic - it will try:
1. The model you specify in `GEMINI_MODEL`
2. `gemini-pro` (if first fails)
3. `gemini-1.5-pro` (if second fails)

## Quick Fix Steps

1. **Update your `.env` file:**
   ```env
   GEMINI_MODEL=gemini-pro
   ```

2. **Restart your Flask app:**
   ```bash
   python app.py
   ```

3. **Check the console output** - it will show which model is being used:
   ```
   Using Gemini model: gemini-3-flash-preview
   ```

## Available Gemini Models

Based on your API key and region, these models might be available:

| Model Name | Description | Use Case |
|------------|-------------|----------|
| `gemini-3-flash-preview` | Latest preview model | ✅ **Recommended** - Works well, good balance |
| `gemini-pro` | Standard model | Most compatible, works everywhere |
| `gemini-1.5-pro` | Advanced model | Better quality, may not be available in all regions |
| `gemini-1.5-flash` | Fast model | Fast responses, may not be available in all regions |
| `gemini-2.0-flash-exp` | Latest experimental | Newest features, experimental |

## Why This Happened

- Different API versions support different models
- Some models are region-specific
- The `gemini-1.5-flash` model might not be available in your region yet
- Your API key might have access to different models

## Verification

After updating, you should see in your Flask console:
```
Using Gemini model: gemini-3-flash-preview
Firebase initialized with bucket: ...
```

And the AI advice should work without errors! ✅

## Still Having Issues?

1. **Check your API key:**
   - Go to https://makersuite.google.com/app/apikey
   - Make sure your key is valid
   - Some keys have restrictions on which models they can use

2. **Check available models:**
   - Visit https://aistudio.google.com
   - See which models are available in your region

3. **Update the library:**
   ```bash
   pip install --upgrade google-generativeai
   ```

The code now handles this automatically with fallbacks, so it should work! 🎉
