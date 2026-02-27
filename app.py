from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"





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
    c.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reviewer_id INTEGER,
        reviewee_id INTEGER,
        rating INTEGER,
        comment TEXT,
        request_id INTEGER
    )
""")
    conn.commit()
    conn.close()

    


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
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
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT credits FROM users WHERE id=?", (session["user_id"],))
    credits = c.fetchone()[0]
    conn.close()

    return render_template("dashboard.html", username=session["username"], credits=credits)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/post", methods=["GET", "POST"])
def post():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        listing_type = request.form["type"]
        price = request.form["price"]
        available_from = request.form["available_from"]
        available_to = request.form["available_to"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO listings 
            (title, description, type, price, owner_id, available_from, available_to)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            listing_type,
            price,
            session["user_id"],
            available_from,
            available_to
        ))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("post.html")


@app.route("/browse")
def browse():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        SELECT listings.id, title, description, type, price, username,available_from, available_to
        FROM listings
        JOIN users ON listings.owner_id = users.id
        WHERE available=1 AND owner_id != ?
    """, (session["user_id"],))
    
    listings = c.fetchall()
    conn.close()

    return render_template("browse.html", listings=listings)



@app.route("/request/<int:listing_id>")
def request_listing(listing_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # 🔹 Get listing price
    c.execute("SELECT price FROM listings WHERE id=?", (listing_id,))
    listing = c.fetchone()

    if not listing:
        conn.close()
        return "Listing not found"

    price = listing[0]

    # 🔹 Get buyer credits
    c.execute("SELECT credits FROM users WHERE id=?", (session["user_id"],))
    buyer_credits = c.fetchone()[0]

    # 🔥 CHECK HERE
    if buyer_credits < price:
        conn.close()
        return "You do not have enough credits to request this item!"

    # 🔹 Insert request
    c.execute("""
        INSERT INTO requests (listing_id, requester_id, status)
        VALUES (?, ?, 'Pending')
    """, (listing_id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect("/my_requests")


@app.route("/my_listings")
def my_listings():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT requests.id, listings.title, users.username, requests.status
        FROM requests
        JOIN listings ON requests.listing_id = listings.id
        JOIN users ON requests.requester_id = users.id
        WHERE listings.owner_id = ?
    """, (session["user_id"],))

    requests_data = c.fetchall()
    conn.close()

    return render_template("my_listings.html", requests=requests_data)



@app.route("/my_requests")
def my_requests():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        SELECT requests.id, listings.title, requests.status
        FROM requests
        JOIN listings ON requests.listing_id = listings.id
        WHERE requests.requester_id = ?
    """, (session["user_id"],))

    requests_data = c.fetchall()
    conn.close()

    return render_template("my_requests.html", requests=requests_data)

@app.route("/accept/<int:request_id>")
def accept_request(request_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Get listing price, owner, requester
    c.execute("""
        SELECT listings.price, listings.owner_id, requests.requester_id, listings.id
        FROM requests
        JOIN listings ON requests.listing_id = listings.id
        WHERE requests.id = ?
    """, (request_id,))

    data = c.fetchone()

    if data:
        price, owner_id, requester_id, listing_id = data

    # 🔥 Step 1: Get buyer credits
        c.execute("SELECT credits FROM users WHERE id=?", (requester_id,))
        buyer_credits = c.fetchone()[0]

    # 🔥 Step 2: Check if enough credits
        if buyer_credits < price:
            conn.close()
            return "Buyer does not have enough credits!"

    # 🔥 Step 3: Then transfer credits
        c.execute("UPDATE users SET credits = credits - ? WHERE id = ?", (price, requester_id))

        c.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (price, owner_id))

        c.execute("UPDATE requests SET status='Accepted' WHERE id = ?", (request_id,))

        c.execute("UPDATE listings SET available = 0 WHERE id = ?", (listing_id,))

    conn.commit()
    conn.close()

    return redirect("/my_listings")


@app.route("/reject/<int:request_id>")
def reject_request(request_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE requests SET status='Rejected' WHERE id = ?", (request_id,))

    conn.commit()
    conn.close()

    return redirect("/my_listings")



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


@app.route("/delete/<int:listing_id>")
def delete_listing(listing_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # 🔒 Ensure only owner can delete
    c.execute("SELECT owner_id FROM listings WHERE id=?", (listing_id,))
    result = c.fetchone()

    if not result:
        conn.close()
        return "Listing not found"

    owner_id = result[0]

    if owner_id != session["user_id"]:
        conn.close()
        return "Unauthorized"

    # 🔥 Delete related requests first (important)
    c.execute("DELETE FROM requests WHERE listing_id=?", (listing_id,))

    # 🔥 Then delete listing
    c.execute("DELETE FROM listings WHERE id=?", (listing_id,))

    conn.commit()
    conn.close()

    return redirect("/my_posts")



    return redirect("/my_requests")


if __name__ == "__main__":
    init_db()   # 👈 THIS LINE creates table if not exists
    app.run(debug=True)