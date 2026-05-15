from flask import Flask, render_template, request, redirect, session, url_for
import json
import sqlite3

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = "super_secret_key"

# --------------------------
# LOAD ITEMS
# --------------------------
with open("items_data.json") as f:
    items_data = json.load(f)

# --------------------------
# DATABASE SETUP
# --------------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE
        )
    """)

    # Order History
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            items TEXT,
            total INTEGER,
            payment_method TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# --------------------------
# LOGIN REQUIRED
# --------------------------
def login_required(f):
    def wrap(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# --------------------------
# ADMIN LOGIN
# --------------------------h
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def admin_required(f):
    def wrap(*args, **kwargs):
        if "admin" not in session:
            return redirect("/admin")
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    message = ""
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
        else:
            message = "Invalid admin login!"
    return render_template("admin_login.html", message=message)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html", items=items_data)

# --------------------------
# ADMIN ADD PRODUCT
# --------------------------
@app.route("/admin/add", methods=["GET", "POST"])
@admin_required
def add_product():
    if request.method == "POST":
        name = request.form["name"]

        items_data[name] = {
            "price": int(request.form["price"]),
            "category": request.form["category"],
            "image": request.form["image"],
            "description": request.form["description"]
        }

        with open("items_data.json", "w") as f:
            json.dump(items_data, f, indent=2)

        return redirect("/admin/dashboard")

    return render_template("add_product.html")

# --------------------------
# ADMIN EDIT PRODUCT
# --------------------------
@app.route("/admin/edit/<name>", methods=["GET", "POST"])
@admin_required
def edit_product(name):
    item = items_data[name]

    if request.method == "POST":
        new_name = request.form["name"]

        items_data.pop(name)  # remove old name

        items_data[new_name] = {
            "price": int(request.form["price"]),
            "category": request.form["category"],
            "image": request.form["image"],
            "description": request.form["description"]
        }

        with open("items_data.json", "w") as f:
            json.dump(items_data, f, indent=2)

        return redirect("/admin/dashboard")

    return render_template("edit_product.html", item=item, name=name)

# --------------------------
# ADMIN DELETE PRODUCT
# --------------------------
@app.route("/admin/delete/<name>")
@admin_required
def delete_product(name):
    items_data.pop(name)
    with open("items_data.json", "w") as f:
        json.dump(items_data, f, indent=2)
    return redirect("/admin/dashboard")

# --------------------------
# USER SIGNUP
# --------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = ""
    if request.method == "POST":
        user = request.form["username"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users(username) VALUES (?)", (user,))
            conn.commit()
            return redirect("/login")
        except:
            message = "Username already exists!"

        conn.close()

    return render_template("signup.html", message=message)

# --------------------------
# USER LOGIN
# --------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        user = request.form["username"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (user,))
        found = c.fetchone()
        conn.close()

        if found:
            session["user"] = user
            return redirect("/")
        else:
            message = "User not found!"

    return render_template("login.html", message=message)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# --------------------------
# HOME PAGE
# --------------------------
@app.route("/")
@login_required
def home():
    return render_template("index.html", items=items_data)


# --------------------------
# CATEGORY PAGES
# --------------------------
@app.route("/category/<cat>")
@login_required
def by_category(cat):
    filtered = {
        name: data
        for name, data in items_data.items()
        if data["category"].strip().lower() == cat.strip().lower()
    }
    return render_template("index.html", items=filtered)

# --------------------------
# CART PAGE
# --------------------------
@app.route("/cart")
@login_required
def cart():
    return render_template("cart.html", items_data=items_data)


# --------------------------
# BILLING PAGE → Payment
# --------------------------
@app.route("/billing", methods=["POST"])
@login_required
def billing():
    items = json.loads(request.form["items"])  # <-- now items is a list, correct
    total = int(request.form["total"])

    session["cart"] = items
    session["total"] = total

    return render_template("payment.html", items=items, total=total)




# --------------------------
# PAYMENT CONFIRM PAGE
# --------------------------
@app.route("/payment_done", methods=["POST"])
@login_required
def payment_done():
    username = session.get("user")
    cart = session.get("cart", [])
    total = session.get("total", 0)
    payment_method = request.form.get("payment_method")

    # Save last order details in session
    session["last_order"] = {
        "cart": cart,
        "total": total,
        "payment": payment_method
    }

    # Store order in database
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO order_history (username, items, total, payment_method)
        VALUES (?, ?, ?, ?)
    """, (username, json.dumps(cart), total, payment_method))
    conn.commit()
    conn.close()

    # ⭐ VERY IMPORTANT — THIS SHOWS THE RECEIPT PAGE AFTER PAYMENT
    return redirect(url_for("receipt"))



@app.route("/receipt")
@login_required
def receipt():
    order = session.get("last_order")
    if not order:
        return "No recent order!"
    return render_template("receipt.html", order=order)





# --------------------------
# RUN APP
# --------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
