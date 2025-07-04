# migrate_schema.py
import sqlite3

def add_column_if_not_exists(cursor, table, column, col_type):
    # Check if the column already exists
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"✅ Added '{column}' to '{table}' table.")
    else:
        print(f"ℹ️ Column '{column}' already exists in '{table}'.")

def migrate_db():
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()

    # Add 'username' to both tables if not present
    add_column_if_not_exists(cursor, "income", "username", "TEXT")
    add_column_if_not_exists(cursor, "expenses", "username", "TEXT")

    conn.commit()
    conn.close()
    print("✅ Migration completed.")

if __name__ == "__main__":
    migrate_db()
