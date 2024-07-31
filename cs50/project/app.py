from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd

# Configure application
app = Flask(__name__)
app.debug = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///bookswap.db")

# Google Books API
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"

# Get book data from API response
def process_books_data(items):
    books = []  # List to store book info
    authors = []  # List to store authors

    # Iterate through each item (book) in the API response
    for item in items:
        authors = volume_info.get('authors', [])  # Get authors, default to empty list if not present
        title = volume_info.get('title', 'No Title')  # Get title, default to 'No Title' if not present

        authors.extend(authors)  # Add authors to the list of all authors

        # Add book information to books list
        books.append({
            'authors': format_authors(authors),
            'title': title,
        })

    return books, authors


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def home():
    """Redirect to the login page if not logged in"""
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html")


@app.route("/search",methods=['GET','POST'])
@login_required
def search():
    """Homepage to search for books"""
    # User reached route via GET
    if request.method == "GET":
        return render_template("index.html")

    # User reached route via POST
    if request.method == "POST":
        print(request.headers)
        data = request.get_json()
        if data is None:
            return apology("Invalid data", 400)

        user_id = session["user_id"]
        title = data.get('title', 'No title provided')
        author = data.get('author', 'No author provided')
        image = data.get('image', 'No image provided')
        # Insert data into database
        try:
            db.execute("INSERT INTO books (user_id, title, author, image_url) VALUES(?, ?, ?, ?)",
                       user_id, title, author, image)
        except ValueError:
            return apology("Invalid entry", 400)

        return redirect("/library")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # If user is already logged in
    if "user_id" in session:
        return redirect("/")

    # User reached route via POST
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via GET
    if request.method == "GET":
        return render_template("register.html")

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Add username into database
        username = request.form.get("username")
        if not username:
            return apology("Must provide username", 400)

        # Validate password
        password = request.form.get("password")
        if not password:
            return apology("Must provide password", 400)

        confirmation = request.form.get("confirmation")
        if not confirmation:
            return apology("Must confirm password", 400)

        if password != confirmation:
            return apology("Passwords do not match", 400)

        hash = generate_password_hash(password)

        # Add username and password into database
        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
        except ValueError:
            return apology("Username already exists", 400)

        return redirect("/login")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via GET
    if request.method == "GET":
        return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell a book"""
    # Get user's books
    user_id = session["user_id"]
    books = []
    rows = db.execute("SELECT title, author FROM books WHERE user_id = ?", user_id)
    for row in rows:
        book_dict = {"title": row["title"], "author": row["author"]}
        books.append(book_dict)

    # User reached route via GET
    if request.method == "GET":
        return render_template("sell.html", books=books)


@app.route("/library")
@login_required
def library():
    """Show personal library of books"""
    user_id = session["user_id"]
    rows = db.execute("SELECT image_url, title, author FROM books WHERE user_id = ?", user_id)
    return render_template("library.html", rows=rows)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
