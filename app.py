from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime 

app = Flask(__name__)
app.secret_key = "secret123"


def connect_db():
    return sqlite3.connect("expenses.db")

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        category TEXT,
        description TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return "Invalid credentials"

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    conn = connect_db()
    cursor = conn.cursor()

    user_id = session['user_id']

    # 📋 Fetch all expenses of user
    cursor.execute("""
        SELECT id, user_id, amount, category, description, date
        FROM expenses
        WHERE user_id=?
        ORDER BY date DESC
    """, (user_id,))
    expenses = cursor.fetchall()

    # 📊 Monthly chart data
    cursor.execute("""
        SELECT strftime('%m', date) AS month, SUM(amount)
        FROM expenses
        WHERE user_id=?
        GROUP BY month
        ORDER BY month
    """, (user_id,))
    data = cursor.fetchall()

    # ✅ Convert safely to lists (VERY IMPORTANT)
    months = []
    totals = []

    for row in data:
        # Convert month number → readable (01 → Jan)
        month_num = row[0]
        month_name = datetime.strptime(month_num, "%m").strftime("%b")

        months.append(month_name)
        totals.append(row[1])

    # 💰 Total spending
    cursor.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id=?
    """, (user_id,))
    total_expense = cursor.fetchone()[0] or 0

    conn.close()

    return render_template(
        "dashboard.html",
        expenses=expenses,
        months=months,
        totals=totals,
        total_expense=total_expense
    )

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')

    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']

    # 📅 current date
    date = datetime.now().strftime("%Y-%m-%d")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
        (session['user_id'], amount, category, description, date)
    )

    conn.commit()
    conn.close()

    return redirect('/')


@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM expenses WHERE id=? AND user_id=?",
        (id, session['user_id'])
    )

    conn.commit()
    conn.close()

    return redirect('/')


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)