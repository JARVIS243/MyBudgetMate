import sqlite3
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime, timedelta

def create_table():
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()

    # Create income table with username
    c.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            amount REAL,
            source TEXT,
            date TEXT
        )
    ''')

    # Create expenses table with username
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            amount REAL,
            category TEXT,
            note TEXT,
            date TEXT
        )
    ''')

    # Create savings goal table
    c.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            username TEXT PRIMARY KEY,
            amount REAL
        )
    ''')

    conn.commit()
    conn.close()

def create_recurring_tables():
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS recurring_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            amount REAL,
            source TEXT,
            frequency TEXT,
            start_date TEXT,
            last_added TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS recurring_expense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            amount REAL,
            category TEXT,
            note TEXT,
            frequency TEXT,
            start_date TEXT,
            last_added TEXT
        )
    ''')
    conn.commit()
    conn.close()

def apply_due_recurring(username):
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()

    today = datetime.today().date()

    # INCOME
    for row in c.execute("SELECT * FROM recurring_income WHERE username=?", (username,)).fetchall():
        last = datetime.strptime(row[6], "%Y-%m-%d").date() if row[6] else datetime.strptime(row[5], "%Y-%m-%d").date()
        due = False
        if row[4] == "daily" and last < today:
            due = True
        elif row[4] == "weekly" and last + timedelta(days=7) <= today:
            due = True
        elif row[4] == "monthly" and (last.month != today.month or last.year != today.year):
            due = True
        if due:
            c.execute("INSERT INTO income (username, amount, source, date) VALUES (?, ?, ?, ?)",
                      (username, row[2], row[3], today.strftime("%Y-%m-%d")))
            c.execute("UPDATE recurring_income SET last_added=? WHERE id=?", (today.strftime("%Y-%m-%d"), row[0]))

    # EXPENSE
    for row in c.execute("SELECT * FROM recurring_expense WHERE username=?", (username,)).fetchall():
        last = datetime.strptime(row[7], "%Y-%m-%d").date() if row[7] else datetime.strptime(row[5], "%Y-%m-%d").date()
        due = False
        if row[5] == "daily" and last < today:
            due = True
        elif row[5] == "weekly" and last + timedelta(days=7) <= today:
            due = True
        elif row[5] == "monthly" and (last.month != today.month or last.year != today.year):
            due = True
        if due:
            c.execute("INSERT INTO expenses (username, amount, category, note, date) VALUES (?, ?, ?, ?, ?)",
                      (username, row[2], row[3], row[4], today.strftime("%Y-%m-%d")))
            c.execute("UPDATE recurring_expense SET last_added=? WHERE id=?", (today.strftime("%Y-%m-%d"), row[0]))

    conn.commit()
    conn.close()

def add_income(amount, source, date, username):
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute("INSERT INTO income (username, amount, source, date) VALUES (?, ?, ?, ?)",
              (username, amount, source, date))
    conn.commit()
    conn.close()

def add_expense(amount, category, note, date, username):
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute("INSERT INTO expenses (username, amount, category, note, date) VALUES (?, ?, ?, ?, ?)",
              (username, amount, category, note, date))
    conn.commit()
    conn.close()

def get_summary(username):
    conn = sqlite3.connect("budget.db")
    df_income = pd.read_sql_query("SELECT * FROM income WHERE username=?", conn, params=(username,))
    df_expense = pd.read_sql_query("SELECT * FROM expenses WHERE username=?", conn, params=(username,))
    conn.close()

    total_income = df_income['amount'].sum() if not df_income.empty else 0
    total_expense = df_expense['amount'].sum() if not df_expense.empty else 0
    balance = total_income - total_expense

    return total_income, total_expense, balance, df_income, df_expense

def get_expense_by_category(username):
    conn = sqlite3.connect("budget.db")
    df = pd.read_sql_query(
        "SELECT category, SUM(amount) as total FROM expenses WHERE username=? GROUP BY category",
        conn, params=(username,)
    )
    conn.close()
    return df

def filter_income(start_date, end_date, username):
    conn = sqlite3.connect("budget.db")
    query = """
        SELECT * FROM income
        WHERE date BETWEEN ? AND ? AND username=?
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date, username))
    conn.close()
    return df

def filter_expense(start_date, end_date, username, category=None):
    conn = sqlite3.connect("budget.db")
    if category and category != "All":
        query = """
            SELECT * FROM expenses
            WHERE date BETWEEN ? AND ? AND username=? AND category=?
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date, username, category))
    else:
        query = """
            SELECT * FROM expenses
            WHERE date BETWEEN ? AND ? AND username=?
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date, username))
    conn.close()
    return df

def export_to_csv(df, filename="data.csv"):
    return df.to_csv(index=False).encode('utf-8')

def set_savings_goal(username, amount):
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            username TEXT PRIMARY KEY,
            amount REAL
        )
    ''')
    c.execute('''
        INSERT OR REPLACE INTO goals (username, amount) VALUES (?, ?)
    ''', (username, amount))
    conn.commit()
    conn.close()

def get_savings_goal(username):
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute('SELECT amount FROM goals WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def generate_monthly_pdf(username, income_df, expense_df, total_income, total_expense, balance, month_label=""):
    file_path = f"{username}_monthly_report.pdf"
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, f"MyBudgetMate Monthly Report - {month_label}")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 70, f"User: {username}")

    # Summary
    y = height - 120
    c.drawString(50, y, f"Total Income: ₹{total_income:.2f}")
    c.drawString(250, y, f"Total Expense: ₹{total_expense:.2f}")
    c.drawString(450, y, f"Balance: ₹{balance:.2f}")
    y -= 30

    # Income Table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Income Records:")
    y -= 20
    c.setFont("Helvetica", 10)
    for i, row in income_df.iterrows():
        text = f"{row['date']} - ₹{row['amount']} - {row['source']}"
        c.drawString(60, y, text)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    # Expense Table
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Expense Records:")
    y -= 20
    c.setFont("Helvetica", 10)
    for i, row in expense_df.iterrows():
        text = f"{row['date']} - ₹{row['amount']} - {row['category']} ({row['note']})"
        c.drawString(60, y, text)
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    return file_path

def get_budget_tips(username):
    tips = []
    total_income, total_expense, balance, _, _ = get_summary(username)
    goal = get_savings_goal(username)

    if total_expense > total_income:
        tips.append("🚨 You're spending more than you earn! Consider reducing expenses.")

    if goal and balance < goal * 0.5:
        tips.append("💰 You're below 50% of your savings goal. Try saving more this month.")

    if goal is None:
        tips.append("🎯 Set a savings goal to track your monthly progress!")

    cat_df = get_expense_by_category(username)
    if not cat_df.empty:
        highest = cat_df.sort_values(by='total', ascending=False).iloc[0]
        if highest['total'] > total_expense * 0.4:
            tips.append(f"📊 You are spending a lot on {highest['category']} (₹{highest['total']:.2f}). Try to optimize it.")

    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    rec_inc = c.execute("SELECT COUNT(*) FROM recurring_income WHERE username=?", (username,)).fetchone()[0]
    rec_exp = c.execute("SELECT COUNT(*) FROM recurring_expense WHERE username=?", (username,)).fetchone()[0]
    conn.close()
    if rec_inc + rec_exp == 0:
        tips.append("🔁 You haven't set up any recurring income/expenses. Use it to automate tracking.")

    return tips
