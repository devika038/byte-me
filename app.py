from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime



app = Flask(__name__)
app.secret_key = "supersecretkey"
@app.route('/')
def home():
    return render_template('home.html')



# ------------------ DATABASE INIT ------------------

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            credits INTEGER DEFAULT 10
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            type TEXT,
            price INTEGER,
            owner_id INTEGER,
            available INTEGER DEFAULT 1,
            available_from TEXT,
            available_to TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER,
            requester_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'Pending',
            returned INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# ------------------ AUTH ------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ------------------ DASHBOARD ------------------

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT credits FROM users WHERE id=?",
              (session["user_id"],))
    credits = c.fetchone()[0]
    conn.close()

    return render_template("dashboard.html",
                           username=session["username"],
                           credits=credits)


# ------------------ POST LISTING ------------------

@app.route("/post", methods=["GET", "POST"])
def post():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("""
            INSERT INTO listings 
            (title, description, type, price, owner_id, available_from, available_to)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["title"],
            request.form["description"],
            request.form["type"],
            request.form["price"],
            session["user_id"],
            request.form["available_from"],
            request.form["available_to"]
        ))

        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template("post.html")


#---delete
@app.route("/delete/<int:listing_id>", methods=["POST"])
def delete_listing(listing_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Make sure the listing exists and belongs to this user
    c.execute("SELECT owner_id FROM listings WHERE id = ?", (listing_id,))
    row = c.fetchone()

    if row is None:
        conn.close()
        return "Listing not found"

    if row[0] != session["user_id"]:
        conn.close()
        return "Unauthorized"

    # Delete all requests for this listing first
    c.execute("DELETE FROM requests WHERE listing_id = ?", (listing_id,))

    # Delete the listing
    c.execute("DELETE FROM listings WHERE id = ?", (listing_id,))

    conn.commit()
    conn.close()

    return redirect("/my_posts")

# ------------------ BROWSE ------------------

@app.route("/browse")
def browse():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT listings.id, title, description, type, price, username,
               available_from, available_to
        FROM listings
        JOIN users ON listings.owner_id = users.id
        WHERE available=1 AND owner_id != ?
    """, (session["user_id"],))

    listings = c.fetchall()
    conn.close()

    return render_template("browse.html", listings=listings)


# ------------------ REQUEST ITEM ------------------

@app.route("/request/<int:listing_id>", methods=["POST"])
def request_listing(listing_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT price FROM listings WHERE id=?", (listing_id,))
    listing = c.fetchone()

    if not listing:
        conn.close()
        return "Listing not found"

    price = listing[0]

    c.execute("SELECT credits FROM users WHERE id=?",
              (session["user_id"],))
    buyer_credits = c.fetchone()[0]

    if buyer_credits < price:
        conn.close()
        return "Not enough credits"

    c.execute("""
        INSERT INTO requests 
        (listing_id, requester_id, start_date, end_date)
        VALUES (?, ?, ?, ?)
    """, (
        listing_id,
        session["user_id"],
        request.form["start_date"],
        request.form["end_date"]
    ))

    conn.commit()
    conn.close()

    return redirect("/my_requests")


# ------------------ MY REQUESTS ------------------

@app.route("/my_requests")
def my_requests():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT
            requests.id,
            listings.title,
            users.username,
            requests.status
        FROM requests
        JOIN listings ON requests.listing_id = listings.id
        JOIN users ON listings.owner_id = users.id
        WHERE requests.requester_id = ?
    """, (session["user_id"],))

    requests_data = c.fetchall()
    conn.close()

    return render_template("my_requests.html", requests=requests_data)

# ------------------ MY LISTINGS (Incoming Requests) ------------------

@app.route("/my_listings")
def my_listings():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    SELECT
        requests.id,
        listings.title,
        users.username,
        requests.status
    FROM requests
    JOIN listings ON requests.listing_id = listings.id
    JOIN users ON requests.requester_id = users.id
    WHERE listings.owner_id = ?
""", (session["user_id"],))

    requests_data = c.fetchall()
    conn.close()

    return render_template("my_listings.html",
                           requests=requests_data)

# ------------------ MY POSTED LISTINGS ------------------

@app.route("/my_posts")
def my_posts():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT id, title, description, type, price, available
        FROM listings
        WHERE owner_id = ?
    """, (session["user_id"],))

    listings = c.fetchall()
    conn.close()

    return render_template("my_posts.html", listings=listings)


# ------------------ ACCEPT REQUEST ------------------

@app.route("/accept/<int:request_id>")
def accept_request(request_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT listings.price, listings.owner_id,
               requests.requester_id, listings.id
        FROM requests
        JOIN listings ON requests.listing_id = listings.id
        WHERE requests.id = ?
    """, (request_id,))

    data = c.fetchone()

    if not data:
        conn.close()
        return "Invalid request"

    price, owner_id, requester_id, listing_id = data

    c.execute("SELECT credits FROM users WHERE id=?",
              (requester_id,))
    buyer_credits = c.fetchone()[0]

    if buyer_credits < price:
        conn.close()
        return "Buyer does not have enough credits"

    c.execute("UPDATE users SET credits = credits - ? WHERE id=?",
              (price, requester_id))
    c.execute("UPDATE users SET credits = credits + ? WHERE id=?",
              (price, owner_id))

    c.execute("UPDATE requests SET status='Accepted' WHERE id=?",
              (request_id,))
    c.execute("UPDATE listings SET available=0 WHERE id=?",
              (listing_id,))

    conn.commit()
    conn.close()

    return redirect("/my_listings")


# ------------------ REJECT ------------------

@app.route("/reject/<int:request_id>")
def reject_request(request_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE requests SET status='Rejected' WHERE id=?",
              (request_id,))

    conn.commit()
    conn.close()

    return redirect("/my_listings")


# ------------------ RETURN ITEM ------------------

@app.route("/return/<int:request_id>")
def return_item(request_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT end_date, requester_id, listing_id
        FROM requests WHERE id=?
    """, (request_id,))

    data = c.fetchone()

    if not data:
        conn.close()
        return "Invalid request"

    end_date_str, requester_id, listing_id = data

    today = datetime.now().date()
    due_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    if today > due_date:
        late_days = (today - due_date).days
        penalty = late_days * 2
        c.execute("UPDATE users SET credits = credits - ? WHERE id=?",
                  (penalty, requester_id))

    c.execute("UPDATE requests SET returned=1 WHERE id=?",
              (request_id,))
    c.execute("UPDATE listings SET available=1 WHERE id=?",
              (listing_id,))

    conn.commit()
    conn.close()

    return redirect("/my_listings")


# ------------------ RUN ------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)