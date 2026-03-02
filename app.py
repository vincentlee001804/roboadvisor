from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json
from dotenv import load_dotenv

from services.firebase_service import FirebaseService
from services.ai_service import AIService

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'  # Temporary folder for processing
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Initialize Firebase service
try:
    firebase = FirebaseService()
except Exception as e:
    print(f"Warning: Firebase not initialized. Error: {e}")
    print("Make sure FIREBASE_SERVICE_ACCOUNT_PATH is set in .env")
    firebase = None

# Initialize AI service
ai_service = AIService()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_firebase():
    """Initialize Firebase - check if user exists"""
    if firebase:
        user = firebase.get_first_user()
        if not user:
            # Create default user for demo
            firebase.create_user("Demo User", "demo@example.com")

@app.route('/')
def index():
    """Home page / Dashboard"""
    if not firebase:
        flash('Firebase not configured. Please set up Firebase.', 'error')
        return render_template('setup.html')
    
    # For demo, use first user (in production, implement proper auth)
    user = firebase.get_first_user()
    if not user:
        return redirect(url_for('setup'))
    
    # Get recent expenses
    expenses = firebase.get_expenses(user['id'], limit=10)
    
    # Convert date strings to datetime objects for template
    for exp in expenses:
        if isinstance(exp.get('date'), str):
            try:
                exp['date'] = datetime.fromisoformat(exp['date'].replace('Z', '+00:00'))
            except:
                exp['date'] = datetime.now()
        elif hasattr(exp.get('date'), 'timestamp'):
            exp['date'] = datetime.fromtimestamp(exp['date'].timestamp())
    
    # Get budgets
    budgets = firebase.get_budgets(user['id'])
    
    # Add calculated fields to budgets for template
    for budget in budgets:
        spent = firebase.get_budget_spent(user['id'], budget['category'])
        budget['spent'] = spent
        budget['remaining'] = budget['amount'] - spent
        budget['percentage'] = (spent / budget['amount'] * 100) if budget['amount'] > 0 else 0
    
    # Calculate totals
    total_expenses = firebase.get_total_expenses(user['id'])
    
    # Get AI advice - only regenerate if expenses have changed
    recent_advice = None
    if expenses:
        # Get current expense count
        current_expense_count = firebase.get_expense_count(user['id'])
        
        # Get cached advice and expense count when it was generated
        cached_advice, cached_expense_count = firebase.get_cached_advice(user['id'])
        
        # Only regenerate if expense count has changed
        if cached_advice and cached_expense_count == current_expense_count:
            # Use cached advice - expenses haven't changed
            recent_advice = cached_advice
        else:
            # Expenses have changed or no cache exists - generate new advice
            # Create expense objects compatible with AI service with full details
            expense_objects = []
            for exp in expenses:
                class ExpenseObj:
                    def __init__(self, data):
                        self.category = data.get('category', 'Other')
                        self.amount = data.get('amount', 0)
                        self.merchant = data.get('merchant', 'Unknown')
                        self.description = data.get('description', '')
                        self.date = data.get('date', None)
                expense_objects.append(ExpenseObj(exp))
            
            budget_objects = []
            for budget in budgets:
                class BudgetObj:
                    def __init__(self, data, user_id):
                        self.category = data.get('category', 'Other')
                        self.amount = data.get('amount', 0)
                        self.user_id = user_id
                    def get_spent(self, user_id):
                        return firebase.get_budget_spent(user_id, self.category)
                budget_objects.append(BudgetObj(budget, user['id']))
            
            recent_advice = ai_service.get_financial_advice(user['id'], expense_objects, budget_objects)
            
            # Cache the new advice
            if recent_advice:
                firebase.cache_advice(user['id'], recent_advice, current_expense_count)
    
    return render_template('dashboard.html', 
                         user=user, 
                         expenses=expenses, 
                         budgets=budgets,
                         total_expenses=total_expenses,
                         advice=recent_advice)

@app.route('/upload', methods=['GET', 'POST'])
def upload_receipt():
    """Handle receipt/image upload"""
    if not firebase:
        flash('Firebase not configured. Please set up Firebase.', 'error')
        return render_template('upload.html')
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Create uploads directory if it doesn't exist (temporary for processing)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            
            # Get user
            user = firebase.get_first_user()
            if not user:
                flash('User not found', 'error')
                return redirect(url_for('setup'))
            
            # Process image with AI/OCR
            try:
                expense_data = ai_service.extract_expense_from_image(filepath)
                
                # Upload image to Firebase Storage
                storage_path = f"receipts/{user['id']}/{filename}"
                image_url = firebase.upload_file(filepath, storage_path)
                
                # Store image path temporarily in session for edit modal
                # We'll save the expense after user confirms/edits
                expense_data['receipt_image'] = image_url
                expense_data['temp_filepath'] = filepath  # Keep file until confirmed
                
                # Convert date to string for template
                if isinstance(expense_data.get('date'), datetime):
                    expense_data['date'] = expense_data['date'].strftime('%Y-%m-%d')
                
                # Ensure items is a list
                if 'items' not in expense_data or not expense_data['items']:
                    expense_data['items'] = [{
                        'name': expense_data.get('description', 'Item'),
                        'price': expense_data.get('amount', 0)
                    }]
                
                # Render upload page with edit modal
                return render_template('upload.html', 
                                     expense_data=expense_data,
                                     show_edit_modal=True)
            
            except Exception as e:
                flash(f'Error processing image: {str(e)}', 'error')
                # Clean up temporary file on error
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except:
                    pass
                return redirect(request.url)
        
        else:
            flash('Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF)', 'error')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/expenses')
def expenses():
    """View all expenses"""
    if not firebase:
        flash('Firebase not configured. Please set up Firebase.', 'error')
        return redirect(url_for('setup'))
    
    user = firebase.get_first_user()
    if not user:
        return redirect(url_for('setup'))
    
    expenses = firebase.get_expenses(user['id'])
    
    # Convert date strings to datetime objects for template
    for exp in expenses:
        if isinstance(exp.get('date'), str):
            try:
                exp['date'] = datetime.fromisoformat(exp['date'].replace('Z', '+00:00'))
            except:
                exp['date'] = datetime.now()
        elif hasattr(exp.get('date'), 'timestamp'):
            exp['date'] = datetime.fromtimestamp(exp['date'].timestamp())
    
    return render_template('expenses.html', expenses=expenses)

@app.route('/add-expense', methods=['GET', 'POST'])
def add_expense():
    """Manually add an expense (for cases with no receipt)"""
    if not firebase:
        flash('Firebase not configured. Please set up Firebase.', 'error')
        return redirect(url_for('setup'))
    
    user = firebase.get_first_user()
    if not user:
        return redirect(url_for('setup'))
    
    if request.method == 'POST':
        merchant = request.form.get('merchant', '').strip()
        amount_raw = request.form.get('amount', '0').strip()
        category = request.form.get('category', 'Other')
        date_str = request.form.get('date', '').strip()
        description = request.form.get('description', '').strip()
        
        # Basic validation
        try:
            amount = float(amount_raw)
        except ValueError:
            flash('Please enter a valid amount.', 'error')
            return redirect(url_for('add_expense'))
        
        if not merchant:
            flash('Please enter a merchant name.', 'error')
            return redirect(url_for('add_expense'))
        
        # Parse date (default to today)
        try:
            expense_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
        except Exception:
            expense_date = datetime.now()
        
        # Create expense in Firebase
        try:
            firebase.create_expense(
                user_id=user['id'],
                merchant=merchant,
                amount=amount,
                category=category,
                date=expense_date,
                description=description,
                receipt_image=None,
                items=None
            )
            flash('Expense added successfully.', 'success')
            return redirect(url_for('expenses'))
        except Exception as e:
            flash(f'Error adding expense: {str(e)}', 'error')
            return redirect(url_for('add_expense'))
    
    # GET: show form with default date = today
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_expense.html', today=today)

@app.route('/expenses/save', methods=['POST'])
def save_expense():
    """Save expense after user edits (from OCR modal)"""
    if not firebase:
        flash('Firebase not configured.', 'error')
        return redirect(url_for('upload_receipt'))
    
    try:
        data = request.get_json()
        user = firebase.get_first_user()
        if not user:
            flash('User not found', 'error')
            return jsonify({'error': 'User not found'}), 400
        
        # Parse items from JSON
        items = data.get('items', [])
        if isinstance(items, str):
            import json
            items = json.loads(items)
        
        # Calculate total from items if provided
        amount = data.get('amount', 0)
        if items and len(items) > 0:
            # If items provided, sum them up
            calculated_total = sum(float(item.get('price', 0)) for item in items)
            # Use provided amount or calculated total
            amount = float(amount) if amount else calculated_total
        
        # Parse date
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        try:
            expense_date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            expense_date = datetime.now()
        
        # Create expense
        expense_id = firebase.create_expense(
            user_id=user['id'],
            merchant=data.get('merchant', 'Unknown'),
            amount=amount,
            category=data.get('category', 'Other'),
            date=expense_date,
            description=data.get('description', ''),
            receipt_image=data.get('receipt_image', ''),
            items=items
        )
        
        # Clean up temporary file if exists
        temp_filepath = data.get('temp_filepath')
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except:
                pass
        
        return jsonify({'success': True, 'expense_id': expense_id})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/expenses/<expense_id>', methods=['GET'])
def get_expense(expense_id):
    """Get expense details for editing"""
    if not firebase:
        return jsonify({'error': 'Firebase not configured'}), 500
    
    try:
        expense = firebase.get_expense(expense_id)
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404
        
        # Convert date to string for JSON
        if isinstance(expense.get('date'), datetime):
            expense['date'] = expense['date'].strftime('%Y-%m-%d')
        
        return jsonify(expense)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/expenses/<expense_id>', methods=['POST'])
def update_expense(expense_id):
    """Update an existing expense"""
    if not firebase:
        flash('Firebase not configured.', 'error')
        return redirect(url_for('expenses'))
    
    try:
        data = request.get_json()
        
        # Parse items
        items = data.get('items', [])
        if isinstance(items, str):
            import json
            items = json.loads(items)
        
        # Calculate amount from items if provided
        amount = data.get('amount', 0)
        if items and len(items) > 0:
            calculated_total = sum(float(item.get('price', 0)) for item in items)
            amount = float(amount) if amount else calculated_total
        
        # Parse date
        date_str = data.get('date', '')
        expense_date = None
        if date_str:
            try:
                expense_date = datetime.strptime(date_str, '%Y-%m-%d')
            except:
                pass
        
        # Update expense
        firebase.update_expense(
            expense_id=expense_id,
            merchant=data.get('merchant'),
            amount=amount,
            category=data.get('category'),
            date=expense_date,
            description=data.get('description'),
            items=items
        )
        
        # Clear cached advice since expense was updated
        user = firebase.get_first_user()
        if user:
            try:
                firebase.cache_advice(user['id'], None, None)  # Clear cache
            except:
                pass
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/expenses/delete/<expense_id>', methods=['POST'])
def delete_expense(expense_id):
    """Delete an expense"""
    if not firebase:
        flash('Firebase not configured.', 'error')
        return redirect(url_for('expenses'))
    
    try:
        success = firebase.delete_expense(expense_id)
        if success:
            # Clear cached advice since expense was deleted
            user = firebase.get_first_user()
            if user:
                try:
                    firebase.cache_advice(user['id'], None, None)  # Clear cache
                except:
                    pass
            flash('Expense deleted successfully!', 'success')
        else:
            flash('Failed to delete expense.', 'error')
    except Exception as e:
        flash(f'Error deleting expense: {str(e)}', 'error')
    
    return redirect(url_for('expenses'))

@app.route('/budget', methods=['GET', 'POST'])
def budget():
    """Manage budgets"""
    if not firebase:
        flash('Firebase not configured. Please set up Firebase.', 'error')
        return redirect(url_for('setup'))
    
    user = firebase.get_first_user()
    if not user:
        return redirect(url_for('setup'))
    
    if request.method == 'POST':
        category = request.form.get('category')
        amount = float(request.form.get('amount', 0))
        
        # Update or create budget in Firestore
        firebase.create_or_update_budget(user['id'], category, amount)
        
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('budget'))
    
    budgets = firebase.get_budgets(user['id'])
    
    # Add calculated fields to budgets for template compatibility
    for budget in budgets:
        spent = firebase.get_budget_spent(user['id'], budget['category'])
        budget['spent'] = spent
        budget['remaining'] = budget['amount'] - spent
        budget['percentage'] = (spent / budget['amount'] * 100) if budget['amount'] > 0 else 0
    
    return render_template('budget.html', budgets=budgets, user=user, firebase=firebase)

@app.route('/advice')
def advice():
    """Get AI financial advice"""
    if not firebase:
        flash('Firebase not configured. Please set up Firebase.', 'error')
        return redirect(url_for('setup'))
    
    user = firebase.get_first_user()
    if not user:
        return redirect(url_for('setup'))
    
    expenses = firebase.get_expenses(user['id'])
    budgets = firebase.get_budgets(user['id'])
    
    # Convert to objects compatible with AI service with full details
    class ExpenseObj:
        def __init__(self, data):
            self.category = data.get('category', 'Other')
            self.amount = data.get('amount', 0)
            self.merchant = data.get('merchant', 'Unknown')
            self.description = data.get('description', '')
            self.date = data.get('date', None)
    
    class BudgetObj:
        def __init__(self, data, user_id):
            self.category = data.get('category', 'Other')
            self.amount = data.get('amount', 0)
            self.user_id = user_id
        def get_spent(self, user_id):
            return firebase.get_budget_spent(user_id, self.category)
    
    expense_objects = [ExpenseObj(exp) for exp in expenses]
    budget_objects = [BudgetObj(budget, user['id']) for budget in budgets]
    
    advice = ai_service.get_financial_advice(user['id'], expense_objects, budget_objects)
    
    return render_template('advice.html', advice=advice, expenses=expenses, budgets=budgets)

@app.route('/regenerate-advice', methods=['POST'])
def regenerate_advice():
    """Debug endpoint to force regenerate advice"""
    if not firebase:
        return jsonify({'error': 'Firebase not configured'}), 500
    
    try:
        user = firebase.get_first_user()
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        # Clear cached advice
        firebase.cache_advice(user['id'], None, None)
        
        # Get expenses and budgets
        expenses = firebase.get_expenses(user['id'], limit=10)
        budgets = firebase.get_budgets(user['id'])
        
        # Create expense objects
        expense_objects = []
        for exp in expenses:
            class ExpenseObj:
                def __init__(self, data):
                    self.category = data.get('category', 'Other')
                    self.amount = data.get('amount', 0)
                    self.merchant = data.get('merchant', 'Unknown')
                    self.description = data.get('description', '')
                    self.date = data.get('date', None)
            expense_objects.append(ExpenseObj(exp))
        
        budget_objects = []
        for budget in budgets:
            class BudgetObj:
                def __init__(self, data, user_id):
                    self.category = data.get('category', 'Other')
                    self.amount = data.get('amount', 0)
                    self.user_id = user_id
                def get_spent(self, user_id):
                    return firebase.get_budget_spent(user_id, self.category)
            budget_objects.append(BudgetObj(budget, user['id']))
        
        # Generate new advice
        advice = ai_service.get_financial_advice(user['id'], expense_objects, budget_objects)
        
        # Cache it
        current_expense_count = firebase.get_expense_count(user['id'])
        firebase.cache_advice(user['id'], advice, current_expense_count)
        
        return jsonify({'success': True, 'advice': advice})
    except Exception as e:
        import traceback
        print(f"Error regenerating advice: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/clear-advice-cache', methods=['POST'])
def clear_advice_cache():
    """Debug endpoint to clear advice cache"""
    if not firebase:
        return jsonify({'error': 'Firebase not configured'}), 500
    
    try:
        user = firebase.get_first_user()
        if not user:
            return jsonify({'error': 'User not found'}), 400
        
        # Clear cached advice
        firebase.cache_advice(user['id'], None, None)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/bnpl-check', methods=['POST'])
def bnpl_check():
    """Check BNPL offer and provide warning"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No data received',
                'risk_level': 'High',
                'warning_message': 'Unable to analyze offer. No data provided.',
                'total_cost': None,
                'apr': None,
                'recommendation': 'Please check your input and try again.'
            }), 400
        
        bnpl_offer = data.get('offer', {})
        if not bnpl_offer:
            return jsonify({
                'error': 'No offer data found',
                'risk_level': 'High',
                'warning_message': 'Unable to analyze offer. Offer details missing.',
                'total_cost': None,
                'apr': None,
                'recommendation': 'Please fill in all required fields.'
            }), 400
        
        # Debug: print received data
        print(f"Received BNPL offer: {bnpl_offer}")
        
        analysis = ai_service.analyze_bnpl_offer(bnpl_offer)
        return jsonify(analysis)
    except Exception as e:
        import traceback
        print(f"Error in bnpl_check: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'risk_level': 'High',
            'warning_message': f'Unable to analyze offer: {str(e)}',
            'total_cost': None,
            'apr': None,
            'recommendation': 'Please check your input and try again.'
        }), 500

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Initial setup - create user"""
    if not firebase:
        flash('Firebase not configured. Please set up Firebase first. See README for instructions.', 'error')
        return render_template('setup.html')
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        if name and email:
            user_id = firebase.create_user(name, email)
            flash('Setup complete!', 'success')
            return redirect(url_for('index'))
    
    return render_template('setup.html')

if __name__ == '__main__':
    init_firebase()
    app.run(debug=True, host='0.0.0.0', port=5000)
