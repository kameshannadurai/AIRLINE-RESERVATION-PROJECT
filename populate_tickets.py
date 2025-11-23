import qrcode
import sqlite3
import os

DB_NAME = "air_reservation.db"
BASE_URL = "http://127.0.0.1:5000/verify/"   # Change later if deployed

# Make folder
os.makedirs("qr_codes", exist_ok=True)

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

cur.execute("SELECT ticket_num FROM Tickets ORDER BY ticket_num")
rows = cur.fetchall()

print(f"\n📦 Generating {len(rows)} QR codes...\n")

for (ticket,) in rows:
    qr_data = BASE_URL + ticket
    img = qrcode.make(qr_data)
    img.save(f"qr_codes/{ticket}.png")
    print(f"✔ QR Saved → qr_codes/{ticket}.png")

conn.close()

print("\n🎉 COMPLETED — All QR boarding passes generated!\n")
