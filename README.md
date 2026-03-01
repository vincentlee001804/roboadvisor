# AI-Powered Robo-Advisor for Students

A personalized financial management tool designed for students, featuring automated expense tracking via receipt photos and AI-driven financial advice.

## Features

- 📸 **Frictionless Expense Tracking**: Upload receipt photos or e-wallet screenshots
- 🤖 **AI-Powered OCR**: Automatically extracts merchant, amount, date, and category
- 💡 **Proactive Financial Advice**: Personalized spending insights and recommendations
- ⚠️ **BNPL Trap Warning**: Analyzes Buy Now Pay Later offers for hidden costs
- 📊 **Budget Management**: Track spending against monthly budgets
- 📱 **Responsive Web Interface**: Modern, mobile-friendly dashboard

## Tech Stack

- **Frontend**: Flask with Jinja2 templates, Tailwind CSS, Chart.js
- **Backend**: Flask (Python)
- **Database**: Firebase Firestore (cloud NoSQL database)
- **Storage**: Firebase Storage (for receipt images)
- **AI Services**: Google Gemini API (Gemini 1.5 Flash for OCR and advice)

## Setup Instructions

### 1. Clone or Download the Project

```bash
cd "C:\Users\vince\Documents\UTS\BorNEO HackWknd 2026\MVP"
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Firebase

1. **Create Firebase Project:**
   - Go to https://console.firebase.google.com/
   - Click "Add project" and create a new project
   - Enable **Firestore Database** (Start in test mode OR production mode - see below)
   - Enable **Storage** (Start in test mode OR production mode - see below)
   
   **Note:** If you chose production mode, you need to set security rules. See `FIREBASE_PRODUCTION_RULES.md` for instructions.

2. **Get Service Account Key:**
   - Go to Project Settings → Service Accounts
   - Click "Generate new private key"
   - Save the JSON file as `firebase-service-account.json` in the project root
   - **Important:** Add this file to `.gitignore` (already included)

3. **Set Up Environment Variables:**

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3-flash-preview
SECRET_KEY=your-secret-key-here
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
```

**Note about SECRET_KEY:**
- This is a Flask secret key (NOT from Firebase)
- Generate one with: `python -c "import secrets; print(secrets.token_hex(32))"`
- Or use any random string (32+ characters)
- Used for Flask session security

**Note about GEMINI_MODEL:**
- Default: `gemini-3-flash-preview` (works well for most users)
- Other options: `gemini-pro`, `gemini-1.5-pro`, `gemini-1.5-flash`
- The code will automatically fallback to other models if your specified model isn't available

Get your Google Gemini API key from: https://makersuite.google.com/app/apikey

### 5. Run the Application

```bash
python app.py
```

The app will be available at: `http://localhost:5000`

### 6. Initial Setup

On first run, you'll be prompted to create a user account. After that, you can:
- Upload receipts to track expenses
- Set monthly budgets
- View AI-generated financial advice
- Analyze BNPL offers

## Project Structure

```
MVP/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env                  # Environment variables (create this)
├── firebase-service-account.json  # Firebase credentials (create this, add to .gitignore)
├── services/
│   ├── ai_service.py     # Google Gemini API integration
│   └── firebase_service.py  # Firebase Firestore & Storage integration
├── templates/
│   ├── base.html         # Base template
│   ├── dashboard.html    # Main dashboard
│   ├── upload.html       # Receipt upload page
│   ├── expenses.html     # Expense list
│   ├── budget.html       # Budget management
│   ├── advice.html       # AI advice page
│   └── setup.html        # Initial setup
├── static/               # CSS, JS, images (if needed)
└── uploads/              # Uploaded receipt images (auto-created)
```

## Development Notes

### Database

The app uses **Firebase Firestore** for cloud-based data storage. All data (users, expenses, budgets) is stored in Firestore collections. Receipt images are stored in Firebase Storage.

**Firebase Free Tier Limits:**
- Firestore: 50K reads/day, 20K writes/day
- Storage: 5GB storage, 1GB/day downloads
- More than enough for hackathon demos!

### Google Gemini API Usage

- **OCR**: Uses Gemini Pro Vision to extract expense data from images
- **Advice**: Uses Gemini Pro for financial advice generation
- **BNPL Analysis**: Uses Gemini Pro to analyze and warn about BNPL offers
- **Free Tier**: Gemini API offers generous free tier, perfect for hackathons!

### File Uploads

- Maximum file size: 16MB
- Allowed formats: PNG, JPG, JPEG, GIF, WEBP
- Uploads are processed locally, then stored in **Firebase Storage**
- Images are automatically deleted from local `uploads/` folder after upload

## Team Workload Split

1. **Frontend/UI Engineer**: Dashboard UI, image upload, charts
2. **OCR & Data Engineer**: Image processing, data extraction
3. **AI Integration Specialist**: LLM prompts, API integration
4. **Backend Engineer**: Flask routes, API endpoints, data flow
5. **Database & PM**: Schema design, integration, pitch

## Future Enhancements

- User authentication (multi-user support)
- Export expenses to CSV/PDF
- Spending trends and analytics charts
- Mobile app version
- Integration with e-wallet APIs
- Local LLM option (Ollama) for privacy

## License

Created for BorNEO HackWknd 2026 - Case Study 7: AI for Financial Literacy
