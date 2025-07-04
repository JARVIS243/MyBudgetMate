import streamlit as st
import sqlite3

def create_user_table():
    conn = sqlite3.connect("budget.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect("budget.db")
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def validate_login(username, password):
    conn = sqlite3.connect("budget.db")
    result = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
    conn.close()
    return result is not None

def user_exists(username):
    conn = sqlite3.connect("budget.db")
    result = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return result is not None

def login_ui():
    st.title("🔐 MyBudgetMate Login")

    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Passkey", type="password", key="login_pass")

        if st.button("Login"):
            if validate_login(username, password):
                st.session_state["logged_in"] = True
                st.session_state["user"] = username
                st.success(f"✅ Welcome, {username}!")
            else:
                st.error("❌ Invalid credentials")

    with tab2:
        new_user = st.text_input("New Username", key="new_user")
        new_pass = st.text_input("New Passkey", type="password", key="new_pass")

        if st.button("Create Account"):
            if user_exists(new_user):
                st.warning("⚠️ Username already exists")
            elif new_user and new_pass:
                add_user(new_user, new_pass)
                st.success("✅ Account created! Please log in.")
            else:
                st.warning("❗ Fill all fields")
