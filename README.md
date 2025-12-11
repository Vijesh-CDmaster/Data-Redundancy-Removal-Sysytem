# Data Redundancy Removal System

This project is a Flask-based web application that identifies and prevents duplicate data entries using intelligent validation rules. MongoDB is used for persistent storage, and the user interface supports real-time search, record validation, and data management.

---

## Features

* Duplicate detection using hash-based comparison
* Prevention of false positives
* Unique email and phone number validation
* Indian mobile number validation (10 digits, starting with 6/7/8/9)
* Allows multiple users with the same name
* Real-time search across all stored records
* Dashboard displaying total entries, duplicates blocked, and false positives
* RESTful API for all operations
* MongoDB for permanent data storage
* Responsive UI with real-time updates

---

## System Requirements

* Python 3.7 or higher
* MongoDB 4.0 or higher
* Works on Windows, macOS, and Linux
* Any modern browser

---

## Installation

1. Create a new project folder:

```
mkdir data-redundancy-system
cd data-redundancy-system
```

2. Install Python dependencies:

```
pip install flask pymongo
```

For MongoDB Atlas:

```
pip install pymongo[srv]
```

3. Install MongoDB (local or Atlas)

4. Create the folder structure:

```
data-redundancy-system/
├── app.py
├── templates/
│   └── index.html
└── README.md
```

---

## Configuration

MongoDB connection (in app.py):

Local:

```python
MONGO_URI = "mongodb://localhost:27017/"
```

MongoDB Atlas:

```python
MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/"
```

Optional: Change the port number in app.run()

---

## Usage

Start the application:

```
python app.py
```

Open in browser:

```
http://localhost:5000
```

You can:

* Add new entries
* Validate email and phone number
* Automatically detect duplicates
* Search through all records
* Delete entries

---

## API Endpoints

GET /
Returns the main UI page.

POST /api/add_entry
Adds a new entry with validation.

GET /api/get_database
Returns all entries and system stats.

DELETE /api/delete_entry/<entry_id>
Deletes a record.

GET /api/search?q=<query>
Search across all fields.

GET /api/stats
Returns statistics.

DELETE /api/clear_database
Clears all entries from the database.

---

## Database Schema

employees collection:

```json
{
  "id": "ID1702345678901",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "9876543210",
  "timestamp": "2024-12-11T10:30:00"
}
```

stats collection:

```json
{
  "total": 10,
  "duplicates": 5,
  "false_positives": 2
}
```

---

## Validation Rules

Name:

* Required
* Duplicate names allowed

Email:

* Required
* Must be valid format
* Must be unique

Phone:

* Required
* Must be 10 digits
* Must start with 6, 7, 8, or 9
* Must be unique
* Hyphens and spaces are auto-removed

Invalid examples:

* 12345678
* 123456789012
* 5123456789
* 0123456789

---

## Troubleshooting

Pymongo module missing:

```
pip install pymongo
```

MongoDB connection timeout:

* Ensure MongoDB service is running
* Verify connection string
* Check firewall

Authentication errors (Atlas):

* Correct username and password
* Whitelist your IP

Flask issues:

* Template not found → index.html must be inside templates folder
* Port already in use → change port in app.run()

---

## Contributing

1. Fork this project
2. Create a feature branch
3. Commit changes
4. Push and open a pull request
