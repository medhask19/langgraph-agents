import pandas as pd
import sqlite3

# Load CSV
df = pd.read_csv("sales_data.csv")

# Connect to SQLite (creates file if not exists)
conn = sqlite3.connect("sqllite-db/sales.db")

# Write data to table
df.to_sql("sales", conn, if_exists="replace", index=False)

print("✅ Sales data loaded successfully into SQLite database.")