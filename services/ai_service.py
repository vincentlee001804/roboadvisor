import os
import google.generativeai as genai
from datetime import datetime
import json
import re
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
- items: an array of individual items from the receipt, each with "name" and "price" (e.g., [{"name": "Grilled Chicken", "price": 15.50}, {"name": "Fries", "price": 5.00}])

Return ONLY a valid JSON object with these keys: merchant, amount, category, date (YYYY-MM-DD format), description, items (array of objects with name and price).
If items are not clearly listed, create a single item with the total amount.
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
            
            # Ensure items is a list
            if 'items' not in expense_data or not isinstance(expense_data['items'], list):
                # If no items, create one item with the total amount
                expense_data['items'] = [{
                    'name': expense_data.get('description', 'Item'),
                    'price': expense_data.get('amount', 0)
                }]
            else:
                # Ensure all items have name and price as float
                for item in expense_data['items']:
                    if 'price' in item:
                        item['price'] = float(item['price'])
            
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
            # Prepare detailed expense list with merchant, category, and amount
            expense_details = []
            expense_summary = {}
            total_spent = 0
            
            # Store original expenses list for date filtering
            original_expenses_list = list(expenses)
            
            for exp in expenses:
                # Collect individual expense details
                expense_info = {
                    'merchant': getattr(exp, 'merchant', 'Unknown'),
                    'category': exp.category,
                    'amount': exp.amount,
                    'description': getattr(exp, 'description', '') or ''
                }
                expense_details.append(expense_info)
                
                # Also maintain category summary
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
            
            # Filter expenses for current month
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            monthly_expenses = []
            monthly_total = 0
            monthly_summary = {}
            
            # Check each expense's date to filter by current month
            for i, exp in enumerate(expense_details):
                # Try to get date from original expense object
                exp_date = None
                if i < len(original_expenses_list):
                    orig_exp = original_expenses_list[i]
                    if hasattr(orig_exp, 'date'):
                        exp_date = orig_exp.date
                    elif isinstance(orig_exp, dict):
                        exp_date = orig_exp.get('date')
                
                # Include if from current month, or if no date (assume recent)
                include_expense = True
                if exp_date:
                    if isinstance(exp_date, datetime):
                        if not (exp_date.month == current_month and exp_date.year == current_year):
                            include_expense = False
                    elif isinstance(exp_date, str):
                        try:
                            parsed_date = datetime.fromisoformat(exp_date.replace('Z', '+00:00'))
                            if not (parsed_date.month == current_month and parsed_date.year == current_year):
                                include_expense = False
                        except:
                            pass  # Include if can't parse
                
                if include_expense:
                    monthly_expenses.append(exp)
                    monthly_total += exp['amount']
                    cat = exp['category']
                    if cat not in monthly_summary:
                        monthly_summary[cat] = 0
                    monthly_summary[cat] += exp['amount']
            
            # Use monthly data if available, otherwise use all expenses
            if not monthly_expenses:
                monthly_expenses = expense_details
                monthly_total = total_spent
                monthly_summary = expense_summary
            
            # Build merchant list by category for better context
            merchants_by_category = {}
            for exp in monthly_expenses:
                cat = exp['category']
                if cat not in merchants_by_category:
                    merchants_by_category[cat] = []
                merchants_by_category[cat].append({
                    'merchant': exp['merchant'],
                    'amount': exp['amount']
                })
            
            # Build a concise, single-call prompt for Gemini using expense details.
            # We now ask for plain text advice only (no JSON) to avoid partial JSON issues.
            prompt = f"""You are a friendly financial advisor for students.
Analyze the student's recent spending and give short, practical advice.

Recent expenses (JSON list of items with merchant, category, amount, description):
{json.dumps(monthly_expenses, indent=2)}

Spending by category (this month):
{json.dumps(monthly_summary, indent=2)}

Optional budget summary (if any budgets exist):
{json.dumps(budget_summary, indent=2)}

Write 2–3 short sentences of personalized advice, and output ONLY those sentences.
Do NOT include JSON, keys, quotes, bullet points, or any extra labels.
Just return the advice text itself.
"""
            
            # Single Gemini call for advice (let the model decide output length)
            response = self.text_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7
                )
            )
            
            # Extract advice text in a simple, robust way
            content = getattr(response, "text", "") or str(response)
            # Debug: print raw Gemini response to server console for inspection
            print("\n===== Gemini RAW advice response =====")
            print(content)
            print("===== END raw advice response =====\n")
            
            advice_text = content.strip()
            
            # Final sanity check – if still empty or too short, fall back to a safe message
            if not advice_text or len(advice_text) < 5:
                advice_text = "Keep tracking your expenses regularly and set simple monthly budgets."
            
            return advice_text
        
        except Exception as e:
            return f"Unable to generate advice at this time. Error: {str(e)}"
    
    def analyze_bnpl_offer(self, bnpl_offer):
        """
        Analyze a BNPL offer and provide warnings about hidden costs
        """
        try:
            # Extract offer details with defaults
            purchase_amount = float(bnpl_offer.get('purchase_amount', 0))
            num_payments = int(bnpl_offer.get('num_payments', 1))
            interest_rate = float(bnpl_offer.get('interest_rate', 0))
            fees = float(bnpl_offer.get('fees', 0))
            
            # Calculate basic values first
            payment_amount = purchase_amount / num_payments if num_payments > 0 else purchase_amount
            total_interest = (purchase_amount * interest_rate / 100) if interest_rate > 0 else 0
            total_cost = purchase_amount + total_interest + fees
            
            # Calculate APR (simplified)
            if num_payments > 0 and purchase_amount > 0:
                # Simple APR calculation
                monthly_rate = interest_rate / 100 / 12 if interest_rate > 0 else 0
                apr = (total_interest / purchase_amount) * (12 / num_payments) * 100 if num_payments > 0 else 0
            else:
                apr = 0
            
            # Determine risk level
            if apr > 20 or total_cost > purchase_amount * 1.2:
                risk_level = 'High'
            elif apr > 10 or total_cost > purchase_amount * 1.1:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
            
            # Create prompt for AI analysis
            prompt = f"""Analyze this Buy Now Pay Later (BNPL) offer for a student:

Purchase Amount: ${purchase_amount:.2f}
Number of Payments: {num_payments}
Interest Rate: {interest_rate}%
Additional Fees: ${fees:.2f}

Calculated Values:
- Total Cost: ${total_cost:.2f}
- Effective APR: {apr:.2f}%
- Risk Level: {risk_level}

Provide a clear warning message and recommendation for a student considering this offer.
Keep it concise (2-3 sentences) and student-friendly.

Return a JSON object with these exact keys: total_cost (number), apr (number), risk_level (string: Low/Medium/High), warning_message (string), recommendation (string)."""
            
            # Use the same model as other features (gemini-3-flash-preview with fallback)
            full_prompt = """You are a financial advisor specializing in debt management for students. Analyze BNPL offers and provide clear warnings.

""" + prompt + """

IMPORTANT: Return ONLY a valid JSON object with these exact keys: total_cost, apr, risk_level, warning_message, recommendation.
Do not include any markdown formatting, just the raw JSON."""
            
            # Try with the configured model (should be gemini-3-flash-preview)
            try:
                response = self.text_model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=300,
                        temperature=0.5
                    )
                )
                content = response.text.strip()
            except Exception as e:
                print(f"Error calling AI model: {e}")
                # Fallback: use calculated values only
                raise Exception(f"AI model error: {str(e)}")
            
            # Robust JSON parsing (same approach as expense extraction)
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
            
            # Parse JSON response with multiple attempts
            ai_result = None
            try:
                ai_result = json.loads(content)
            except json.JSONDecodeError:
                # Try to fix common JSON issues
                # Remove any trailing commas
                content = content.replace(',}', '}').replace(',]', ']')
                try:
                    ai_result = json.loads(content)
                except json.JSONDecodeError:
                    # Try to extract just the values we need using regex or string parsing
                    # Extract values using regex
                    total_cost_match = re.search(r'"total_cost"\s*:\s*([0-9.]+)', content)
                    apr_match = re.search(r'"apr"\s*:\s*([0-9.]+)', content)
                    risk_match = re.search(r'"risk_level"\s*:\s*"([^"]+)"', content)
                    warning_match = re.search(r'"warning_message"\s*:\s*"([^"]+)"', content)
                    recommendation_match = re.search(r'"recommendation"\s*:\s*"([^"]+)"', content)
                    
                    ai_result = {
                        'total_cost': float(total_cost_match.group(1)) if total_cost_match else total_cost,
                        'apr': float(apr_match.group(1)) if apr_match else apr,
                        'risk_level': risk_match.group(1) if risk_match else risk_level,
                        'warning_message': warning_match.group(1) if warning_match else 'Please review this offer carefully.',
                        'recommendation': recommendation_match.group(1) if recommendation_match else 'Consider saving up instead of using BNPL.'
                    }
            
            # Merge calculated values with AI response (use calculated values as fallback)
            result = {
                'total_cost': float(ai_result.get('total_cost', total_cost)) if ai_result else total_cost,
                'apr': float(ai_result.get('apr', apr)) if ai_result else apr,
                'risk_level': ai_result.get('risk_level', risk_level) if ai_result else risk_level,
                'warning_message': ai_result.get('warning_message', 'Please review this offer carefully.') if ai_result else 'Please review this offer carefully.',
                'recommendation': ai_result.get('recommendation', 'Consider saving up instead of using BNPL.') if ai_result else 'Consider saving up instead of using BNPL.'
            }
            
            return result
        
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return calculated values
            print(f"JSON decode error: {e}")
            print(f"Response content: {content if 'content' in locals() else 'N/A'}")
            return {
                'total_cost': total_cost if 'total_cost' in locals() else None,
                'apr': apr if 'apr' in locals() else None,
                'risk_level': risk_level if 'risk_level' in locals() else 'High',
                'warning_message': f'Unable to parse AI response. Calculated total cost: ${total_cost:.2f}',
                'recommendation': 'Please review this offer carefully before proceeding.'
            }
        except Exception as e:
            import traceback
            print(f"Error in analyze_bnpl_offer: {str(e)}")
            print(traceback.format_exc())
            # Return calculated values even if AI fails
            if 'total_cost' in locals():
                return {
                    'total_cost': total_cost,
                    'apr': apr if 'apr' in locals() else 0,
                    'risk_level': risk_level if 'risk_level' in locals() else 'High',
                    'warning_message': f'Analysis error: {str(e)}. Calculated values shown.',
                    'recommendation': 'Please review this offer carefully before proceeding.'
                }
            else:
                return {
                    'error': str(e),
                    'risk_level': 'High',
                    'warning_message': 'Unable to analyze offer. Please check your input values.',
                    'total_cost': None,
                    'apr': None,
                    'recommendation': 'Please verify all fields are filled correctly.'
                }
