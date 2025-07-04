import streamlit as st
from datetime import date
import matplotlib.pyplot as plt

from auth import login_ui, create_user_table
from functions import (
    create_table,
    create_recurring_tables,
    apply_due_recurring,
    add_income,
    add_expense,
    get_summary,
    get_expense_by_category,
    filter_income,
    filter_expense,
    export_to_csv,
    get_savings_goal,
    set_savings_goal,
    generate_monthly_pdf,
    get_budget_tips
)

# Setup
st.set_page_config(page_title="MyBudgetMate", layout="centered")
st.markdown("""
    <style>
        body {
            background-color: #0f0f0f;
            color: #e0e0e0;
        }
        .stApp {
            background-color: #111;
        }
        .modern-title {
            font-family: 'Segoe UI', sans-serif;
            font-size: 48px;
            color: white;
            position: relative;
            display: inline-block;
        }
        .modern-title::after {
            content: '';
            position: absolute;
            width: 100%;
            transform: scaleX(0);
            height: 3px;
            bottom: -6px;
            left: 0;
            background: linear-gradient(to right, #00f2ff, #8f00ff);
            transform-origin: bottom right;
            transition: transform 0.4s ease-out;
        }
        .modern-title:hover::after {
            transform: scaleX(1);
            transform-origin: bottom left;
        }
    </style>
""", unsafe_allow_html=True)
create_user_table()

# Session init
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Login screen
if not st.session_state["logged_in"]:
    login_ui()
    st.stop()

# App starts here
create_table()
create_recurring_tables()
username = st.session_state["user"]
apply_due_recurring(username)

st.markdown("""
    <div style="text-align: center; margin-top: -40px; margin-bottom: 20px;">
        <h1 class="modern-title">💸 MyBudgetMate</h1>
        <div style="font-size: 16px; color: #ddd; font-style: italic;">Paisaannu Sookshichu Chilavakkuka Elle Nammuk Jeevikkan ee Kalathu Paadannu ✌🏻</div>
    </div>
""", unsafe_allow_html=True)
st.caption(f"🔐 Logged in as: `{username}`")

mode = st.sidebar.selectbox("Choose Action", ["➕ Add Income", "➖ Add Expense", "📊 View Summary"])

# ➕ Add Income
if mode == "➕ Add Income":
    st.header("➕ Add Income")
    amount = st.number_input("Amount", min_value=0.0, step=10.0)
    source = st.text_input("Source", placeholder="e.g. Salary, Gift")
    in_date = st.date_input("Date", value=date.today())
    if st.button("Save Income"):
        if amount and source:
            add_income(amount, source, in_date.strftime("%Y-%m-%d"), username)
            st.success("✅ Income added!")
        else:
            st.warning("Please fill all fields.")

# ➖ Add Expense
elif mode == "➖ Add Expense":
    st.header("➖ Add Expense")
    amount = st.number_input("Amount", min_value=0.0, step=10.0)
    category = st.selectbox("Category", ["Food", "Transport", "Rent", "Shopping", "Other"])
    note = st.text_input("Note", placeholder="e.g. Bus fare, Lunch")
    ex_date = st.date_input("Date", value=date.today())
    if st.button("Save Expense"):
        if amount and category:
            add_expense(amount, category, note, ex_date.strftime("%Y-%m-%d"), username)
            st.success("✅ Expense added!")
        else:
            st.warning("Please fill all fields.")

# 📊 View Summary
elif mode == "📊 View Summary":
    st.header("📊 Budget Summary")

    total_income, total_expense, balance, df_income, df_expense = get_summary(username)

    # 🎯 Set Savings Goal
    with st.expander("🎯 Monthly Savings Goal"):
        current_goal = get_savings_goal(username)
        new_goal = st.number_input("Set Monthly Goal (₹)", value=current_goal or 0.0, step=100.0)
        if st.button("💾 Save Goal"):
            set_savings_goal(username, new_goal)
            st.success("✅ Goal saved!")

    # 🧮 Show goal progress
    if current_goal:
        progress = balance / current_goal if current_goal != 0 else 0
        if progress < 0:
            st.error(f"🚨 Overspent! ₹{abs(balance):.2f} over the goal ₹{current_goal:.2f}")
        elif progress >= 1:
            st.success(f"🎉 Goal Reached! Saved ₹{balance:.2f} of ₹{current_goal:.2f}")
        else:
            st.info(f"Progress: ₹{balance:.2f} / ₹{current_goal:.2f}")
            st.progress(min(progress, 1.0))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"₹{total_income:.2f}")
    col2.metric("Total Expense", f"₹{total_expense:.2f}")
    col3.metric("Balance", f"₹{balance:.2f}")

    st.subheader("📌 Expense by Category")
    df_cat = get_expense_by_category(username)
    if not df_cat.empty:
        fig, ax = plt.subplots()
        ax.pie(df_cat['total'], labels=df_cat['category'], autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)
    else:
        st.info("No expense data to show chart.")

    st.markdown("### 📅 Filter by Date / Category")
    col1, col2 = st.columns(2)
    start = col1.date_input("From Date", value=date(2024, 1, 1))
    end = col2.date_input("To Date", value=date.today())
    filter_cat = st.selectbox("Expense Category", ["All", "Food", "Transport", "Rent", "Shopping", "Other"])

    if st.button("🔍 Apply Filters"):
        f_income = filter_income(start, end, username)
        f_expense = filter_expense(start, end, username, filter_cat)

        st.subheader("📋 Filtered Income")
        st.download_button(
            "⬇️ Download Filtered Income",
            export_to_csv(f_income),
            file_name="filtered_income.csv",
            mime="text/csv"
        )
        st.dataframe(f_income.sort_values("date", ascending=False))

        st.subheader("📋 Filtered Expenses")
        st.download_button(
            "⬇️ Download Filtered Expenses",
            export_to_csv(f_expense),
            file_name="filtered_expense.csv",
            mime="text/csv"
        )
        st.dataframe(f_expense.sort_values("date", ascending=False))

    st.subheader("⬇️ Export Full Data")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Download Income CSV", export_to_csv(df_income), file_name="income.csv")
    with col2:
        st.download_button("📥 Download Expense CSV", export_to_csv(df_expense), file_name="expenses.csv")

    st.subheader("📄 Monthly PDF Report")
    if st.button("📥 Download PDF Report"):
        month_label = date.today().strftime("%B %Y")
        path = generate_monthly_pdf(username, df_income, df_expense, total_income, total_expense, balance, month_label)
        with open(path, "rb") as f:
            st.download_button(
                label="📄 Download Cheyiyam Ningalude Chilavukal (PDF)",
                data=f,
                file_name=path,
                mime="application/pdf"
            )

    st.subheader("Kurachu Upadhesham Aavam 😁")
    tips = get_budget_tips(username)
    if tips:
        for tip in tips:
            st.info(tip)
    else:
        st.success("🎉 You're doing great! No suggestions right now.")

    st.subheader("📋 Recent Transactions")
    with st.expander("Income Records"):
        st.dataframe(df_income.sort_values("date", ascending=False))
    with st.expander("Expense Records"):
        st.dataframe(df_expense.sort_values("date", ascending=False))

# Logout
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    st.experimental_rerun()

# Footer
st.markdown("""
    <hr style="margin-top:50px; border: none; height: 1px; background: #444;">
    <div style="text-align:center; color:#999; font-size: 14px; margin-top: 10px;">
        © 2025 | Published by Aju Krishna
    </div>
""", unsafe_allow_html=True)
