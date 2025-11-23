from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# ---------------- Database helpers ---------------- #

def create_connection():
    # check_same_thread=False allows SQLite to be used in Flask dev server
    conn = sqlite3.connect('air_reservation.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row  # so we can access columns by name
    return conn


def init_db():
    with create_connection() as conn:
        cursor = conn.cursor()

        # Passengers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Passengers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                phone TEXT NOT NULL,
                passenger_id TEXT UNIQUE NOT NULL
            )
        ''')

        # Flights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flight_id TEXT UNIQUE NOT NULL,
                terminal TEXT,
                ticket TEXT,
                num_flights INTEGER
            )
        ''')

        # Tickets table (base definition – for new DBs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_num TEXT UNIQUE NOT NULL,
                seat_num TEXT,
                airline_name TEXT,
                flight_num TEXT,
                terminal TEXT,
                departure_time TEXT,
                boarding_end_time TEXT
            )
        ''')

        # ✅ Ensure ALL needed columns exist even for OLD DBs
        cursor.execute("PRAGMA table_info(Tickets)")
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]

        # Columns we must have for your project
        required_extra_cols = {
            "seat_num": "TEXT",
            "airline_name": "TEXT",
            "flight_num": "TEXT",
            "terminal": "TEXT",
            "departure_time": "TEXT",
            "boarding_end_time": "TEXT"
        }

        for col_name, col_type in required_extra_cols.items():
            if col_name not in col_names:
                cursor.execute(f"ALTER TABLE Tickets ADD COLUMN {col_name} {col_type}")
                print(f"✅ Added missing column '{col_name}' to Tickets table")

        conn.commit()

        # Planes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Planes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                arrival TEXT,
                departure TEXT,
                plane_num TEXT UNIQUE NOT NULL,
                seats INTEGER,
                size TEXT
            )
        ''')

        conn.commit()


# ---------------- Routes ---------------- #

@app.route('/')
def index():
    return render_template('index.html')


# ------- Add Passenger ------- #
@app.route('/add_passenger', methods=['POST'])
def add_passenger():
    name = request.form['name']
    dob = request.form['dob']
    phone = request.form['phone']
    passenger_id = request.form['passenger_id']

    # Phone number validation: exactly 10 digits
    if not phone.isdigit() or len(phone) != 10:
        return render_template('error.html', message="Phone number must be exactly 10 digits.")

    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Passengers (name, dob, phone, passenger_id) VALUES (?, ?, ?, ?)",
                (name, dob, phone, passenger_id)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return render_template('error.html', message=f"Passenger ID {passenger_id} already exists!")

    return render_template('success.html', type="Passenger", data={
        "Name": name,
        "Date of Birth": dob,
        "Phone": phone,
        "Passenger ID": passenger_id
    })


# ------- Add Flight ------- #
@app.route('/add_flight', methods=['POST'])
def add_flight():
    flight_id = request.form['flight_id']
    terminal = request.form['terminal']
    ticket = request.form['ticket']

    # Validate num_flights as integer
    try:
        num_flights = int(request.form['num_flights'])
    except ValueError:
        return render_template('error.html', message="Number of flights must be a valid number.")

    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Flights (flight_id, terminal, ticket, num_flights) VALUES (?, ?, ?, ?)",
                (flight_id, terminal, ticket, num_flights)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        # Flight ID already exists
        return render_template('error.html', message=f"Flight ID {flight_id} already exists!")

    return render_template('success.html', type="Flight", data={
        "Flight ID": flight_id,
        "Terminal": terminal,
        "Ticket": ticket,
        "Number of Flights": num_flights
    })


# ------- View Ticket Info (ticket_no + seat_no from form) ------- #
@app.route('/ticket_info', methods=['POST'])
def ticket_info():
    ticket_num = request.form['ticket_num']
    seat_num = request.form['seat_num']

    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                ticket_num,
                seat_num,
                airline_name,
                flight_num,
                terminal,
                departure_time,
                boarding_end_time
            FROM Tickets
            WHERE ticket_num = ? AND seat_num = ?
        """, (ticket_num, seat_num))
        row = cursor.fetchone()

    if row is None:
        # Use same template but show invalid (so JS + sounds work)
        return render_template(
            'ticket_info.html',
            valid=False,
            ticket=ticket_num
        )

    data = {
        "Ticket Number": row["ticket_num"],
        "Seat Number": row["seat_num"],
        "Airline": row["airline_name"],
        "Flight Number": row["flight_num"],
        "Terminal": row["terminal"],
        "Departure Time": row["departure_time"],
        "Boarding End Time": row["boarding_end_time"]
    }

    return render_template('ticket_info.html', valid=True, data=data)


# ------- QR VERIFY: /verify/<ticket_num> for QR code / mobile scan ------- #
@app.route('/verify/<ticket_num>')
def verify_ticket(ticket_num):
    with create_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                ticket_num,
                seat_num,
                airline_name,
                flight_num,
                terminal,
                departure_time,
                boarding_end_time
            FROM Tickets
            WHERE ticket_num = ?
        """, (ticket_num,))
        row = cursor.fetchone()

    if row is None:
        # Invalid / fake ticket
        return render_template(
            'ticket_info.html',
            valid=False,
            ticket=ticket_num
        )

    data = {
        "Ticket Number": row["ticket_num"],
        "Seat Number": row["seat_num"],
        "Airline": row["airline_name"],
        "Flight Number": row["flight_num"],
        "Terminal": row["terminal"],
        "Departure Time": row["departure_time"],
        "Boarding End Time": row["boarding_end_time"]
    }

    return render_template('ticket_info.html', valid=True, data=data)


@app.route('/scan')
def scan_page():
    return render_template("scan.html")


# ------- Add Plane ------- #
@app.route('/add_plane', methods=['POST'])
def add_plane():
    arrival = request.form['arrival']
    departure = request.form['departure']
    plane_num = request.form['plane_num']
    size = request.form['size']

    # Validate seats as integer
    try:
        seats = int(request.form['seats'])
    except ValueError:
        return render_template('error.html', message="Seats must be a valid number.")

    try:
        with create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Planes (arrival, departure, plane_num, seats, size) VALUES (?, ?, ?, ?, ?)",
                (arrival, departure, plane_num, seats, size)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        # Plane Number already exists
        return render_template('error.html', message=f"Plane Number {plane_num} already exists!")

    return render_template('success.html', type="Plane", data={
        "Plane Number": plane_num,
        "Arrival": arrival,
        "Departure": departure,
        "Seats": seats,
        "Size": size
    })


# ---------------- Main ---------------- #

# ---------------- Main ---------------- #

# Run DB migrations / create tables when the app is imported (Render + gunicorn)
init_db()

if __name__ == "__main__":
    # For local development only
    app.run(debug=True)

