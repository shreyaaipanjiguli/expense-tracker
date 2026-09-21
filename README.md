# Expense Tracker

A Flask-based personal expense tracker that allows users to securely register, log in, manage expenses, track budgets, and analyze spending by category and month.

## Features

- User registration and login
- Password hashing using Werkzeug
- Session-based authentication
- Add and delete expenses
- Monthly expense filtering
- Budget tracking
- Budget usage indicator
- Category-wise expense analysis
- Total spending and average expense calculation
- SQLite database for local data storage
- Environment-based configuration using `.env`

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS
- **Database:** SQLite
- **Authentication:** Flask sessions + Werkzeug password hashing
- **Configuration:** python-dotenv

## Project Structure

```text
expense-tracker/
│
├── static/
│   └── style.css
│
├── templates/
│   ├── index.html
│   ├── login.html
│   └── register.html
│
├── app.py
├── init_db.py
├── requirements.txt
├── .gitignore
└── README.md