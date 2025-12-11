from flask import Flask, render_template, request, jsonify
import hashlib
import re
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

# MongoDB Configuration
# Replace 'localhost' with your MongoDB connection string if using MongoDB Atlas
MONGO_URI = "mongodb+srv://viju7122006-db:viju7122006@cluster0.qhsrdgt.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['data_redundancy_db']  # Database name
employees_collection = db['employees']  # Collection name
stats_collection = db['stats']  # Stats collection

# Initialize stats if not exists
if stats_collection.count_documents({}) == 0:
    stats_collection.insert_one({
        'total': 0,
        'duplicates': 0,
        'false_positives': 0
    })

def get_stats():
    """Get current statistics from MongoDB"""
    stats = stats_collection.find_one()
    return {
        'total': stats.get('total', 0),
        'duplicates': stats.get('duplicates', 0),
        'false_positives': stats.get('false_positives', 0)
    }

def update_stats(field, increment=1):
    """Update statistics in MongoDB"""
    stats_collection.update_one(
        {},
        {'$inc': {field: increment}}
    )

def hash_data(data):
    """Create a hash for duplicate detection - using only email and phone"""
    hash_string = f"{data['email']}|{data['phone']}".lower().strip()
    return hashlib.md5(hash_string.encode()).hexdigest()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone format - Indian mobile numbers (10 digits)"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if exactly 10 digits
    if len(digits_only) != 10:
        return False
    
    # Check if starts with 6, 7, 8, or 9 (valid Indian mobile prefixes)
    if digits_only[0] not in ['6', '7', '8', '9']:
        return False
    
    return True

def validate_entry(entry):
    """Validate new entry against existing database"""
    # Check for required fields
    if not entry.get('name') or not entry.get('email') or not entry.get('phone'):
        return {
            'valid': False,
            'type': 'incomplete',
            'message': 'All fields are required'
        }
    
    # Validate email format
    if not validate_email(entry['email']):
        return {
            'valid': False,
            'type': 'invalid',
            'message': 'Invalid email format'
        }
    
    # Validate phone format
    if not validate_phone(entry['phone']):
        return {
            'valid': False,
            'type': 'invalid',
            'message': 'Invalid phone format. Enter 10-digit Indian mobile number (starting with 6, 7, 8, or 9)'
        }
    
    # Check for email duplicates (email must be unique)
    existing_email = employees_collection.find_one({
        'email': {'$regex': f'^{re.escape(entry["email"])}$', '$options': 'i'}
    })
    
    if existing_email:
        return {
            'valid': False,
            'type': 'email_duplicate',
            'message': f'Email already exists in database (used by {existing_email["name"]})',
            'duplicate': {
                'id': existing_email['id'],
                'name': existing_email['name'],
                'email': existing_email['email'],
                'phone': existing_email['phone']
            }
        }
    
    # Check for phone duplicates (phone must be unique)
    normalized_entry_phone = re.sub(r'\D', '', entry['phone'])
    all_employees = employees_collection.find()
    
    for item in all_employees:
        normalized_item_phone = re.sub(r'\D', '', item['phone'])
        if normalized_item_phone == normalized_entry_phone:
            return {
                'valid': False,
                'type': 'phone_duplicate',
                'message': f'Phone number already exists in database (used by {item["name"]})',
                'duplicate': {
                    'id': item['id'],
                    'name': item['name'],
                    'email': item['email'],
                    'phone': item['phone']
                }
            }
    
    # Check for ID conflicts
    if entry.get('id'):
        existing_id = employees_collection.find_one({'id': entry['id']})
        if existing_id:
            return {
                'valid': False,
                'type': 'id_conflict',
                'message': 'ID already exists'
            }
    
    return {
        'valid': True,
        'type': 'unique',
        'message': 'Entry is unique and valid (same name allowed)'
    }

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/add_entry', methods=['POST'])
def add_entry():
    """Add a new entry to the database"""
    data = request.json
    validation = validate_entry(data)
    
    if validation['valid']:
        # Generate ID if not provided
        entry_id = data.get('id') or f"ID{int(datetime.now().timestamp() * 1000)}"
        
        entry = {
            'id': entry_id,
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'timestamp': datetime.now().isoformat()
        }
        
        # Insert into MongoDB
        employees_collection.insert_one(entry)
        update_stats('total', 1)
        
        # Remove MongoDB's _id field from response
        entry.pop('_id', None)
        
        return jsonify({
            'success': True,
            'validation': validation,
            'entry': entry,
            'stats': get_stats()
        })
    else:
        # Track blocked duplicates
        if validation['type'] in ['duplicate', 'email_duplicate', 'phone_duplicate']:
            update_stats('duplicates', 1)
        
        return jsonify({
            'success': False,
            'validation': validation,
            'stats': get_stats()
        })

@app.route('/api/get_database', methods=['GET'])
def get_database():
    """Get all database entries"""
    employees = list(employees_collection.find({}, {'_id': 0}))
    return jsonify({
        'database': employees,
        'stats': get_stats()
    })

@app.route('/api/delete_entry/<entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """Delete an entry from the database"""
    result = employees_collection.delete_one({'id': entry_id})
    
    if result.deleted_count > 0:
        # Update total count
        total_count = employees_collection.count_documents({})
        stats_collection.update_one({}, {'$set': {'total': total_count}})
    
    return jsonify({
        'success': True,
        'stats': get_stats()
    })

@app.route('/api/search', methods=['GET'])
def search():
    """Search database entries"""
    query = request.args.get('q', '').lower()
    
    if not query:
        results = list(employees_collection.find({}, {'_id': 0}))
    else:
        # Search across all fields
        results = list(employees_collection.find({
            '$or': [
                {'id': {'$regex': query, '$options': 'i'}},
                {'name': {'$regex': query, '$options': 'i'}},
                {'email': {'$regex': query, '$options': 'i'}},
                {'phone': {'$regex': query, '$options': 'i'}}
            ]
        }, {'_id': 0}))
    
    return jsonify({'results': results})

@app.route('/api/stats', methods=['GET'])
def get_stats_endpoint():
    """Get current statistics"""
    return jsonify(get_stats())

@app.route('/api/clear_database', methods=['DELETE'])
def clear_database():
    """Clear all entries from database (for testing)"""
    employees_collection.delete_many({})
    stats_collection.update_one({}, {
        '$set': {
            'total': 0,
            'duplicates': 0,
            'false_positives': 0
        }
    })
    return jsonify({
        'success': True,
        'message': 'Database cleared',
        'stats': get_stats()
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)