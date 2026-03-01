# Hackathon Project: AI-Powered Robo-Advisor for Students

## Domain
**Case Study 7: AI for Financial Literacy** (BorNEO HackWknd 2026)

## 1. The Problem
While digital financial services and payments are expanding rapidly in the ASEAN region, financial literacy levels remain dangerously low. Students and young adults frequently utilize digital wallets and "Buy Now, Pay Later" (BNPL) schemes without a solid understanding of debt management, interest accumulation, or personal financial resilience. This gap leaves them vulnerable to poor financial decisions and economic shocks.

## 2. The Solution
**An AI-Powered Robo-Advisor & Budgeting Tool**
A personalized, low-friction financial management tool designed specifically for students. It removes the tedious manual data entry of traditional budgeting by utilizing automated text extraction and provides proactive, AI-driven financial advice.

### Key Features:
* **Frictionless Expense Tracking:** Users simply snap a photo of a physical receipt or upload a screenshot of an e-wallet transaction. 
* **Automated OCR Processing:** The system automatically extracts the merchant name, date, total amount, and categorizes the expense.
* **Proactive "Robo-Advisor":** An LLM analyzes the spending patterns against the student's budget and offers personalized, highly contextual advice (e.g., "You've spent 40% of your food budget this week. Cooking pasta at home tonight instead of ordering GrabFood will keep you on track.").
* **BNPL Trap Warning:** A feature to evaluate BNPL offers, breaking down hidden interest rates and warning users before they commit to unmanageable micro-debts.

## 3. Software Specifications

### Architecture & Tech Stack

**Frontend (User Interface):**
* **Recommended: Web App** - Since you have 2 weeks, a web app provides better user experience and demo presentation.
    * **Simplest Option:** Flask with Jinja2 templates (server-side rendering). Build everything in one Flask app - backend + frontend together. Use vanilla JavaScript for interactivity and Chart.js for visualizations. This keeps everything simple and avoids separate frontend/backend complexity.
    * **Modern Option (if team is comfortable):** Next.js (React) with Tailwind CSS. Better for responsive design and modern UI, but requires separate frontend/backend setup. Use Recharts or Chart.js for expense visualizations.
* **Alternative:** Telegram Bot - Fastest to prototype, but less impressive for demo. Use `python-telegram-bot` library.

**Backend (Core Logic & API):**
* **Language:** Python 3.x
* **Framework:** 
    * **If using Flask templates:** **Flask** - perfect for server-side rendering, everything in one app.
    * **If using Next.js frontend:** **Flask** or **FastAPI** - create REST API endpoints. FastAPI provides automatic docs, but Flask is simpler.
* **Hosting:** **Render** (free tier, easiest setup) or **Railway** (even simpler, auto-deploys from GitHub). For Next.js, use **Vercel** (free, optimized for Next.js).

**AI & Core Services:**
* **OCR Engine:** 
    * **Simplest:** Use OpenAI's Vision API (GPT-4 Vision) - it can read receipts directly AND generate advice in one call, reducing complexity.
    * **Alternative:** Google Cloud Vision API (free tier: 1,000 requests/month) or **EasyOCR** (free, open-source, no API keys needed).
* **LLM Integration:** 
    * **Recommended:** OpenAI API (gpt-4o-mini or gpt-4o) - simplest to integrate, handles both OCR and advice generation. Use structured prompts for consistent output.
    * **If budget-conscious:** Start with OpenAI for demo, mention local LLM (Ollama) as future privacy enhancement in pitch.

**Database:**
* **Recommended:** **SQLite** for everything (dev + demo). Zero setup, works perfectly for hackathon demos. Only upgrade to PostgreSQL if you need multi-user support (unlikely for a hackathon demo).
* **Optional:** Use **JSON files** for ultra-simple MVP - store user data as `{user_id}.json`. Upgrade to SQLite when you need queries.

### Suggested Team Workload Split (5 Members)
1.  **Frontend/UI Engineer:** Develops the web dashboard UI, implements image upload functionality, creates expense visualization charts, and ensures mobile-responsive design.
2.  **OCR & Data Engineer:** Handles image processing, text extraction from receipts, data parsing, and JSON formatting for expense data.
3.  **AI Integration Specialist:** Manages the LLM prompts, context windows, and API connections to generate personalized financial advice. Fine-tunes prompts for consistent, actionable advice.
4.  **Backend Engineer:** Builds the Python API endpoints (or Flask routes if using templates), handles file uploads, integrates OCR and AI services, and manages data flow between frontend and database.
5.  **Database & Project Manager:** Designs the database schema, implements data models, ensures smooth integration across all components, and crafts the final hackathon pitch/presentation.