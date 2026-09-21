from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import sqlite3
load_dotenv()

app = Flask(__name__)

# secret key is required by flask to encrypt session cookies (keep users logged in safely)
app.secret_key = os.getenv("SECRET_KEY")
def get_db_connection():
    conn = sqlite3.connect("expenses.db")
    return conn

# --- AUTHENTICATION ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        # Encrypt the raw password into a secure hash
        hashed_password = generate_password_hash(password)
        
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            # Redirect to login page after successful registration
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            # Triggered if the username already exists in SQLite
            conn.close()
            return render_template('register.html', error="Username already exists! Choose another.")
            
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        # Verify user exists and the submitted password matches the database hash
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password!")
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    # Clear all user data from the Flask session cookie
    session.clear()
    return redirect(url_for('login'))

# Route 1: Display Expense
@app.route('/')
def index():
    # 1. Access Control: Redirect to login if user is not logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    selected_month = request.args.get('month', '')
    
    try:
        budget_limit = float(request.args.get('budget', 10000))
    except ValueError:
        budget_limit = 10000.0

    conn = get_db_connection()
    cursor = conn.cursor()

    # 2. Fetch months filtered by logged-in user
    cursor.execute("""
        SELECT DISTINCT strftime('%Y-%m', date) 
        FROM expenses 
        WHERE user_id = ? AND date IS NOT NULL 
        ORDER BY strftime('%Y-%m', date) DESC
    """, (user_id,))
    available_months = [row[0] for row in cursor.fetchall() if row[0]]

    # 3. Fetch expenses filtered by logged-in user
    if selected_month:
        cursor.execute("SELECT * FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? ORDER BY date DESC, id DESC", (user_id, selected_month))
        expenses = cursor.fetchall()

        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ? GROUP BY category", (user_id, selected_month))
        category_data = cursor.fetchall()
    else:
        cursor.execute("SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC", (user_id,))
        expenses = cursor.fetchall()

        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = ? GROUP BY category", (user_id,))
        category_data = cursor.fetchall()

    # Note: expense[2] is amount because column 1 is user_id now
    total_spent = sum(expense[2] for expense in expenses)
    total_count = len(expenses)
    avg_spent = total_spent / total_count if total_count > 0 else 0

    budget_used_pct = min((total_spent / budget_limit) * 100, 100) if budget_limit > 0 else 0

    chart_labels = [row[0] for row in category_data]
    chart_values = [row[1] for row in category_data]

    conn.close()

    if total_spent > budget_limit:
        bar_color = '#f87171'  # Red
    elif budget_used_pct >= 80:
        bar_color = '#fb923c'  # Orange
    else:
        bar_color = '#34d399'  # Green

    return render_template(
        'index.html',
        username=session.get('username'),
        expenses=expenses,
        total_spent=total_spent,
        total_count=total_count,
        avg_spent=avg_spent,
        chart_labels=chart_labels,
        chart_values=chart_values,
        available_months=available_months,
        selected_month=selected_month,
        budget_limit=budget_limit,
        budget_used_pct=budget_used_pct,
        bar_color=bar_color
    )


# Route 2: Add Expense
@app.route("/add", methods=["POST"])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    amount = request.form["amount"]
    category = request.form["category"]
    description = request.form["description"]
    date = request.form["date"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, description, date)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


# Route 3: Delete Expense
@app.route("/delete/<int:id>")
def delete_expense(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure user can only delete their own items
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)