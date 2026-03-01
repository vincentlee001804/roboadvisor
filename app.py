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
    
    # Get AI advice - convert expenses to dict-like format for AI service
    recent_advice = None
    if expenses:
        # Create expense objects compatible with AI service
        expense_objects = []
        for exp in expenses:
            class ExpenseObj:
                def __init__(self, data):
                    self.category = data.get('category', 'Other')
                    self.amount = data.get('amount', 0)
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
                
                # Create expense record in Firestore
                expense_id = firebase.create_expense(
                    user_id=user['id'],
                    merchant=expense_data.get('merchant', 'Unknown'),
                    amount=expense_data.get('amount', 0),
                    category=expense_data.get('category', 'Other'),
                    date=expense_data.get('date', datetime.now()),
                    description=expense_data.get('description', ''),
                    receipt_image=image_url  # Store Firebase Storage URL
                )
                
                # Clean up temporary file
                try:
                    os.remove(filepath)
                except:
                    pass
                
                flash('Expense added successfully!', 'success')
                return redirect(url_for('index'))
            
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

@app.route('/expenses/delete/<expense_id>', methods=['POST'])
def delete_expense(expense_id):
    """Delete an expense"""
    if not firebase:
        flash('Firebase not configured.', 'error')
        return redirect(url_for('expenses'))
    
    try:
        success = firebase.delete_expense(expense_id)
        if success:
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
    
    # Convert to objects compatible with AI service
    class ExpenseObj:
        def __init__(self, data):
            self.category = data.get('category', 'Other')
            self.amount = data.get('amount', 0)
    
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

@app.route('/bnpl-check', methods=['POST'])
def bnpl_check():
    """Check BNPL offer and provide warning"""
    data = request.get_json()
    bnpl_offer = data.get('offer', {})
    
    try:
        analysis = ai_service.analyze_bnpl_offer(bnpl_offer)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
