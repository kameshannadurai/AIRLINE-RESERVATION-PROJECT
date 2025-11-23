import sqlite3

DB_NAME = "air_reservation.db"

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

print("🔍 Current Tickets table columns:")
cur.execute("PRAGMA table_info(Tickets)")
cols = cur.fetchall()
for c in cols:
    print(" -", c[1])

# Try to add airline_name column if it doesn't exist
col_names = [c[1] for c in cols]
if "airline_name" not in col_names:
    print("\nAdding missing column 'airline_name' to Tickets...")
    cur.execute("ALTER TABLE Tickets ADD COLUMN airline_name TEXT;")
    conn.commit()
    print("✅ Column 'airline_name' added.")
else:
    print("\n✅ 'airline_name' column already exists.")

conn.close()
print("\nDone.")
