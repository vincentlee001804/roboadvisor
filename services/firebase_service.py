"""
Firebase Service - Alternative to SQLite for cloud storage
Use this if you want to migrate to Firebase Firestore + Storage
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime
import json

class FirebaseService:
    """Service for Firebase Firestore and Storage integration"""
    
    def __init__(self):
        # Initialize Firebase Admin SDK
        service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', 'firebase-service-account.json')
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Firebase service account file not found: {service_account_path}")
        
        # Read project ID from service account JSON
        import json as json_lib
        with open(service_account_path, 'r') as f:
            service_account_data = json_lib.load(f)
            project_id = service_account_data.get('project_id')
        
        cred = credentials.Certificate(service_account_path)
        
        # Initialize only if not already initialized
        if not firebase_admin._apps:
            # Try both bucket name formats (newer projects use .firebasestorage.app)
            # The Admin SDK will use the correct one automatically
            bucket_name = f"{project_id}.appspot.com"
            firebase_admin.initialize_app(cred, {
                'storageBucket': bucket_name
            })
            print(f"Firebase initialized with bucket: {bucket_name}")
        
        self.db = firestore.client()
        
        # Get bucket - try both formats
        # Newer Firebase projects use .firebasestorage.app instead of .appspot.com
        bucket_names = [
            f"{project_id}.firebasestorage.app",  # New format
            f"{project_id}.appspot.com"            # Old format
        ]
        
        self.bucket = None
        for bucket_name in bucket_names:
            try:
                self.bucket = storage.bucket(bucket_name)
                # Test if bucket exists by trying to access it
                self.bucket.reload()
                print(f"Firebase Storage bucket connected: {bucket_name}")
                break
            except Exception as e:
                continue
        
        if self.bucket is None:
            error_msg = f"Could not access Storage bucket. Tried: {', '.join(bucket_names)}"
            print(f"Warning: {error_msg}")
            print("Make sure Firebase Storage is enabled in Firebase Console:")
            print("1. Go to Firebase Console → Build → Storage")
            print("2. Click 'Get started'")
            print("3. Set up security rules (see FIREBASE_PRODUCTION_RULES.md)")
            raise Exception(error_msg)
    
    # User Operations
    def create_user(self, name, email):
        """Create a new user"""
        user_ref = self.db.collection('users').document()
        user_data = {
            'name': name,
            'email': email,
            'created_at': firestore.SERVER_TIMESTAMP
        }
        user_ref.set(user_data)
        return user_ref.id
    
    def get_user(self, user_id=None, email=None):
        """Get user by ID or email"""
        if user_id:
            doc = self.db.collection('users').document(user_id).get()
            if doc.exists:
                return {'id': doc.id, **doc.to_dict()}
        elif email:
            docs = self.db.collection('users').where('email', '==', email).limit(1).stream()
            for doc in docs:
                return {'id': doc.id, **doc.to_dict()}
        return None
    
    def get_first_user(self):
        """Get first user (for demo purposes)"""
        docs = self.db.collection('users').limit(1).stream()
        for doc in docs:
            return {'id': doc.id, **doc.to_dict()}
        return None
    
    def get_expense_count(self, user_id):
        """Get total count of expenses for a user"""
        expenses = self.db.collection('expenses').where('user_id', '==', user_id).stream()
        return sum(1 for _ in expenses)
    
    def get_cached_advice(self, user_id):
        """Get cached AI advice for user"""
        user_ref = self.db.collection('users').document(user_id)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return user_data.get('cached_advice'), user_data.get('advice_expense_count')
        return None, None
    
    def cache_advice(self, user_id, advice, expense_count):
        """Cache AI advice for user. Pass None for advice to clear cache."""
        user_ref = self.db.collection('users').document(user_id)
        if advice is not None:
            update_data = {
                'cached_advice': advice,
                'advice_expense_count': expense_count,
                'advice_updated_at': firestore.SERVER_TIMESTAMP
            }
            user_ref.update(update_data)
        else:
            # Clear cache by setting to None
            try:
                user_ref.update({
                    'cached_advice': None,
                    'advice_expense_count': None
                })
            except:
                pass
    
    # Expense Operations
    def create_expense(self, user_id, merchant, amount, category, date, description=None, receipt_image=None, items=None):
        """Create a new expense"""
        expense_ref = self.db.collection('expenses').document()
        expense_data = {
            'user_id': user_id,
            'merchant': merchant,
            'amount': float(amount),
            'category': category,
            'date': date if isinstance(date, datetime) else datetime.now(),
            'description': description or '',
            'receipt_image': receipt_image,
            'items': items if items else [],
            'created_at': firestore.SERVER_TIMESTAMP
        }
        expense_ref.set(expense_data)
        return expense_ref.id
    
    def update_expense(self, expense_id, merchant=None, amount=None, category=None, date=None, description=None, items=None):
        """Update an existing expense"""
        expense_ref = self.db.collection('expenses').document(expense_id)
        update_data = {}
        
        if merchant is not None:
            update_data['merchant'] = merchant
        if amount is not None:
            update_data['amount'] = float(amount)
        if category is not None:
            update_data['category'] = category
        if date is not None:
            update_data['date'] = date if isinstance(date, datetime) else datetime.now()
        if description is not None:
            update_data['description'] = description
        if items is not None:
            update_data['items'] = items
        
        update_data['updated_at'] = firestore.SERVER_TIMESTAMP
        expense_ref.update(update_data)
        return True
    
    def get_expense(self, expense_id):
        """Get a single expense by ID"""
        doc = self.db.collection('expenses').document(expense_id).get()
        if doc.exists:
            data = doc.to_dict()
            # Convert Firestore timestamp to datetime
            if 'date' in data:
                if hasattr(data['date'], 'timestamp'):
                    data['date'] = datetime.fromtimestamp(data['date'].timestamp())
                elif hasattr(data['date'], 'seconds'):
                    data['date'] = datetime.fromtimestamp(data['date'].seconds)
            return {'id': doc.id, **data}
        return None
    
    def get_expenses(self, user_id, limit=None):
        """Get expenses for a user"""
        # Note: Firestore requires an index for order_by with where
        # For now, get all and sort in Python (fine for hackathon scale)
        query = self.db.collection('expenses').where('user_id', '==', user_id)
        
        expenses = []
        for doc in query.stream():
            data = doc.to_dict()
            # Convert Firestore timestamp to datetime
            if 'date' in data:
                if hasattr(data['date'], 'timestamp'):
                    data['date'] = datetime.fromtimestamp(data['date'].timestamp())
                elif hasattr(data['date'], 'seconds'):
                    # Firestore Timestamp object
                    data['date'] = datetime.fromtimestamp(data['date'].seconds)
            expenses.append({'id': doc.id, **data})
        
        # Sort by date descending
        expenses.sort(key=lambda x: x.get('date', datetime.min), reverse=True)
        
        if limit:
            expenses = expenses[:limit]
        
        return expenses
    
    def get_total_expenses(self, user_id):
        """Calculate total expenses for a user"""
        expenses = self.get_expenses(user_id)
        return sum(exp.get('amount', 0) for exp in expenses)
    
    def delete_expense(self, expense_id):
        """Delete an expense by ID"""
        try:
            self.db.collection('expenses').document(expense_id).delete()
            return True
        except Exception as e:
            print(f"Error deleting expense: {e}")
            return False
    
    # Budget Operations
    def create_or_update_budget(self, user_id, category, amount):
        """Create or update a budget"""
        # Check if budget exists
        budgets = self.db.collection('budgets').where('user_id', '==', user_id).where('category', '==', category).limit(1).stream()
        
        budget_id = None
        for doc in budgets:
            budget_id = doc.id
            break
        
        budget_data = {
            'user_id': user_id,
            'category': category,
            'amount': float(amount),
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        if budget_id:
            # Update existing
            self.db.collection('budgets').document(budget_id).update(budget_data)
            return budget_id
        else:
            # Create new
            budget_data['created_at'] = firestore.SERVER_TIMESTAMP
            budget_ref = self.db.collection('budgets').document()
            budget_ref.set(budget_data)
            return budget_ref.id
    
    def get_budgets(self, user_id):
        """Get all budgets for a user"""
        budgets = []
        for doc in self.db.collection('budgets').where('user_id', '==', user_id).stream():
            budgets.append({'id': doc.id, **doc.to_dict()})
        return budgets
    
    def get_budget_spent(self, user_id, category):
        """Calculate total spent in a category"""
        expenses = self.db.collection('expenses').where('user_id', '==', user_id).where('category', '==', category).stream()
        return sum(doc.to_dict().get('amount', 0) for doc in expenses)
    
    def set_total_budget(self, user_id, amount):
        """Set or update total monthly budget for a user"""
        # Store total budget with category='_total' to distinguish from category budgets
        budget_data = {
            'user_id': user_id,
            'category': '_total',
            'amount': float(amount),
            'updated_at': firestore.SERVER_TIMESTAMP
        }
        
        # Check if total budget exists
        budgets = self.db.collection('budgets').where('user_id', '==', user_id).where('category', '==', '_total').limit(1).stream()
        
        budget_id = None
        for doc in budgets:
            budget_id = doc.id
            break
        
        if budget_id:
            # Update existing
            self.db.collection('budgets').document(budget_id).update(budget_data)
            return budget_id
        else:
            # Create new
            budget_data['created_at'] = firestore.SERVER_TIMESTAMP
            budget_ref = self.db.collection('budgets').document()
            budget_ref.set(budget_data)
            return budget_ref.id
    
    def get_total_budget(self, user_id):
        """Get total monthly budget for a user"""
        budgets = self.db.collection('budgets').where('user_id', '==', user_id).where('category', '==', '_total').limit(1).stream()
        for doc in budgets:
            return doc.to_dict().get('amount', 0)
        return 0
    
    def get_category_budgets(self, user_id):
        """Get only category-specific budgets (exclude total budget)"""
        budgets = []
        for doc in self.db.collection('budgets').where('user_id', '==', user_id).stream():
            budget_data = doc.to_dict()
            if budget_data.get('category') != '_total':
                budgets.append({'id': doc.id, **budget_data})
        return budgets
    
    # Storage Operations
    def upload_file(self, local_file_path, destination_path):
        """Upload a file to Firebase Storage"""
        try:
            blob = self.bucket.blob(destination_path)
            blob.upload_from_filename(local_file_path)
            blob.make_public()  # Make file publicly accessible
            return blob.public_url
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg or "404" in error_msg:
                raise Exception(
                    f"Firebase Storage bucket not found. Please enable Storage in Firebase Console:\n"
                    f"1. Go to https://console.firebase.google.com/\n"
                    f"2. Select your project\n"
                    f"3. Go to Build → Storage\n"
                    f"4. Click 'Get started' and start in test mode\n"
                    f"Original error: {error_msg}"
                )
            raise
    
    def delete_file(self, file_path):
        """Delete a file from Firebase Storage"""
        blob = self.bucket.blob(file_path)
        blob.delete()
