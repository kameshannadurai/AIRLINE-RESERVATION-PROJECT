import sqlite3
import os
import qrcode

DB_NAME = "air_reservation.db"

# 🔹 Change this later to your ngrok/public URL if you want
BASE_URL = "https://airline-reservation-project-12ch.onrender.com/verify/"


QR_FOLDER = os.path.join("static", "qr")
os.makedirs(QR_FOLDER, exist_ok=True)

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()
cur.execute("SELECT ticket_num FROM Tickets")
rows = cur.fetchall()
conn.close()

for (ticket_num,) in rows:
    url = f"{BASE_URL}/{ticket_num}"
    img = qrcode.make(url)
    file_path = os.path.join(QR_FOLDER, f"{ticket_num}.png")
    img.save(file_path)
    print("Generated QR:", file_path)

