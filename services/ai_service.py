import os
import google.generativeai as genai
from datetime import datetime
import json
from PIL import Image

class AIService:
    """Service for AI/LLM integration using Google Gemini"""
    
    def __init__(self):
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Try different model names - some regions/API versions use different names
        # Common model names: gemini-3-flash-preview, gemini-pro, gemini-1.5-pro, gemini-1.5-flash
        # Default to gemini-3-flash-preview (works well for most users)
        model_name = os.environ.get('GEMINI_MODEL', 'gemini-3-flash-preview')
        
        try:
            # Try to use the specified model
            self.vision_model = genai.GenerativeModel(model_name)
            self.text_model = genai.GenerativeModel(model_name)
            print(f"Using Gemini model: {model_name}")
        except Exception as e:
            # Fallback chain: try different models if the specified one doesn't work
            print(f"Warning: Could not use model '{model_name}': {e}")
            
            # Try gemini-pro
            print("Falling back to 'gemini-pro'")
            try:
                self.vision_model = genai.GenerativeModel('gemini-pro')
                self.text_model = genai.GenerativeModel('gemini-pro')
                print("Successfully using 'gemini-pro'")
            except Exception as e2:
                # Try gemini-1.5-pro
                print(f"Warning: Could not use 'gemini-pro': {e2}")
                print("Trying 'gemini-1.5-pro'")
                try:
                    self.vision_model = genai.GenerativeModel('gemini-1.5-pro')
                    self.text_model = genai.GenerativeModel('gemini-1.5-pro')
                    print("Successfully using 'gemini-1.5-pro'")
                except Exception as e3:
                    # Last resort: try gemini-1.5-flash
                    print(f"Warning: Could not use 'gemini-1.5-pro': {e3}")
                    print("Trying 'gemini-1.5-flash'")
                    self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
                    self.text_model = genai.GenerativeModel('gemini-1.5-flash')
                    print("Successfully using 'gemini-1.5-flash'")
    
    def extract_expense_from_image(self, image_path):
        """
        Extract expense data from receipt/image using Google Gemini Vision API
        Returns: dict with merchant, amount, category, date, description
        """
        try:
            # Load image
            img = Image.open(image_path)
            
            # Create prompt for Gemini
            prompt = """You are an expert at reading receipts and extracting financial data. 
Extract the following information from this receipt:
- merchant/store name
- total amount (as a number, e.g., 25.50)
- category (Food, Transportation, Shopping, Entertainment, Bills, Other)
- date (if visible, otherwise use today's date: """ + datetime.now().strftime('%Y-%m-%d') + """)
- brief description

Return ONLY a valid JSON object with these keys: merchant, amount, category, date (YYYY-MM-DD format), description.
Do not include any markdown formatting, just the raw JSON."""
            
            # Use Gemini Pro Vision to extract expense data
            response = self.vision_model.generate_content([prompt, img])
            content = response.text.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            
            # Try to extract JSON from response
            # Sometimes Gemini returns text with JSON, so we try to find it
            if '{' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                content = content[json_start:json_end]
            
            expense_data = json.loads(content)
            
            # Parse date
            if 'date' in expense_data:
                try:
                    expense_data['date'] = datetime.strptime(expense_data['date'], '%Y-%m-%d')
                except:
                    expense_data['date'] = datetime.now()
            else:
                expense_data['date'] = datetime.now()
            
            # Ensure amount is float
            if 'amount' in expense_data:
                expense_data['amount'] = float(expense_data['amount'])
            
            return expense_data
        
        except Exception as e:
            # Fallback: return default values if extraction fails
            print(f"Error extracting expense: {str(e)}")
            return {
                'merchant': 'Unknown',
                'amount': 0.0,
                'category': 'Other',
                'date': datetime.now(),
                'description': 'Failed to extract receipt data'
            }
    
    def get_financial_advice(self, user_id, expenses, budgets):
        """
        Generate personalized financial advice based on spending patterns
        """
        try:
            # Prepare expense summary
            expense_summary = {}
            total_spent = 0
            for exp in expenses:
                category = exp.category
                if category not in expense_summary:
                    expense_summary[category] = 0
                expense_summary[category] += exp.amount
                total_spent += exp.amount
            
            # Prepare budget summary
            budget_summary = {}
            for budget in budgets:
                spent = budget.get_spent(user_id)
                remaining = budget.get_remaining(user_id)
                budget_summary[budget.category] = {
                    'allocated': budget.amount,
                    'spent': spent,
                    'remaining': remaining,
                    'percentage': (spent / budget.amount * 100) if budget.amount > 0 else 0
                }
            
            # Create prompt for AI
            prompt = f"""You are a friendly financial advisor for students. Analyze this spending data and provide personalized, actionable advice.

Spending Summary (by category):
{json.dumps(expense_summary, indent=2)}

Budget Status:
{json.dumps(budget_summary, indent=2)}

Total Spent: ${total_spent:.2f}

Provide:
1. A brief overview of spending patterns
2. Specific, actionable advice (e.g., "You've spent 40% of your food budget this week. Cooking pasta at home tonight instead of ordering GrabFood will keep you on track.")
3. Any warnings about overspending
4. Tips for saving money

Keep it friendly, concise, and student-focused. Format as a short paragraph (2-3 sentences)."""
            
            # Use Gemini Pro for text generation
            full_prompt = """You are a helpful financial advisor for students. Provide friendly, actionable advice.

""" + prompt
            
            response = self.text_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=300,
                    temperature=0.7
                )
            )
            
            return response.text.strip()
        
        except Exception as e:
            return f"Unable to generate advice at this time. Error: {str(e)}"
    
    def analyze_bnpl_offer(self, bnpl_offer):
        """
        Analyze a BNPL offer and provide warnings about hidden costs
        """
        try:
            prompt = f"""Analyze this Buy Now Pay Later (BNPL) offer and provide a warning about potential hidden costs:

Offer Details:
{json.dumps(bnpl_offer, indent=2)}

Calculate:
1. Total amount to be paid (including all fees/interest)
2. Effective interest rate (APR)
3. Risk level (Low/Medium/High)
4. Clear warning message for students

Return a JSON object with: total_cost, apr, risk_level, warning_message, recommendation"""
            
            # Use Gemini Pro for BNPL analysis
            full_prompt = """You are a financial advisor specializing in debt management for students.

""" + prompt + """

IMPORTANT: Return ONLY a valid JSON object with these exact keys: total_cost, apr, risk_level, warning_message, recommendation.
Do not include any markdown formatting, just the raw JSON."""
            
            response = self.text_model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=400,
                    temperature=0.5
                )
            )
            
            content = response.text.strip()
            # Remove markdown code blocks if present
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
            
            # Try to extract JSON from response
            if '{' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                content = content[json_start:json_end]
            
            return json.loads(content)
        
        except Exception as e:
            return {
                'error': str(e),
                'risk_level': 'High',
                'warning_message': 'Unable to analyze offer. Proceed with caution.'
            }
