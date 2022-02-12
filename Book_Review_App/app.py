from flask import Flask
import os

import traceback
import logging
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify,make_response
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from apiservice import get_book_data

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

if __name__ == '__main__':
   app.run()

@app.route("/")
def index():
    if session.get('username') is None:
        return redirect("/login")
    return render_template("home.html")

@app.route("/register",methods=["GET"])
def render_registeration_page():
    if session.get('username'):
        return redirect("/")
    return render_template("register.html")

@app.route("/register",methods=["POST"])
def register_user():
    try:
        # Extracting values from form input fields
        username = request.form['username']
        password = request.form['psw']

        # Check first if user already exists
        existing_user = db.execute(f"SELECT * from user_accounts where username='{username}'").fetchall()
        if existing_user:
            return render_template("register.html",error_message = "Username already exists")
        
        # Creating user if it does not exists
        db.execute(f"INSERT INTO user_accounts (username,password) values ('{username}','{password}');")
        db.commit()
        return redirect("/login")
    except Exception as e:
        logging.error(traceback.format_exc())
        return render_template("register.html",error_message = "Registeration unsuccessfull,please try again")

@app.route("/login",methods=["GET"])
def render_login_page():
    if session.get('username'):
        return redirect("/")
    return render_template("login.html")

@app.route("/login",methods=["POST"])
def login_user():
    try:
        username = request.form['username']
        password = request.form['psw']
        user = db.execute(f"SELECT * from user_accounts where username='{username}' and password='{password}';").fetchone()
        if user:
            session['username'] = username
            return redirect("/")
        return render_template("login.html",error_message="Unable to login, wrong credentials..")
    except Exception as e:
        logging.error(traceback.format_exc())
        return render_template("login.html",error_message="Unable to login, try again..")

@app.route("/logout")
def logout_user():
    if session.get("username"):
        session.pop("username")
    return redirect("/login")

@app.route("/books",methods=["POST"])
def search_books():
    try:
        if session.get('username') is None:
            return redirect("/login")
        search_query = "%" + request.form['query'].lower() + "%"
        books = db.execute(f"""
                select * from books 
                where lower(isbn) LIKE '{search_query}' or 
                lower(author) LIKE '{search_query}' or 
                lower(title) LIKE '{search_query}'
            """).fetchall()
        return render_template("books.html",books=books)
    except Exception as e:
        logging.error(traceback.format_exc())
        return redirect("/")

@app.route("/review/<string:book_id>",methods=['POST'])
def submit_review(book_id):
    try:
        if session.get('username') is None:
            return redirect("/login")
        user = db.execute(f"""
            select * from user_accounts
            where username = '{session.get('username')}';
        """).fetchone()
        user_reviews = db.execute(f"""
            select * from reviews
            where reviewer_id = {user["id"]} and book_id = {int(book_id)}
        """).fetchone()
        if user_reviews:
            return render_book_info_page(book_id,error_message="Unable to submit a review, since you already submitted a review for this book")
        
        rating = request.form['rating']
        review = request.form['review']
        db.execute(f"""
            Insert into reviews (book_id,reviewer_id,rating,review)
            values ({int(book_id)},{user["id"]},{int(rating)},'{review}')
        """)
        db.commit()
        return render_book_info_page(book_id,message="Review submitted successfully")
    except Exception as e:
        logging.error(traceback.format_exc())
        return redirect("/")

@app.route("/book/<string:book_id>",methods=['GET'])
def render_book_info_page(book_id,message=None,error_message=None):
    try:
        if session.get('username') is None:
            return redirect("/login")
        book_reviews = db.execute(f"""
            select 
            b.id,b.isbn,b.title,b.author,b.year,r.review,r.rating,u.username 
            from books b
            left join reviews r on b.id = r.book_id
            left join user_accounts u on u.id = r.reviewer_id
            where b.id = {int(book_id)}
        """).fetchall()
        if not book_reviews:
            redirect("/")

        ratings = db.execute(f"""
            select 
                count(*) as ratingcount,
                sum(rating) as ratingsum 
                from reviews
                where book_id = {int(book_id)}
            """).fetchone()
        book = book_reviews[0]
        google_api_data = get_book_data(book["isbn"])
        total_ratings = google_api_data["reviewCount"] if google_api_data["reviewCount"] else 0
        average_rating = google_api_data["averageRating"] if google_api_data["averageRating"] else 0
        if ratings["ratingcount"] != 0:
            total_ratings = google_api_data["reviewCount"] + ratings["ratingcount"]
            average_rating = (google_api_data["reviewCount"]*average_rating+ratings["ratingsum"])/total_ratings
        return render_template(
                "book.html",
                book={
                    "id": book["id"],
                    "isbn": book["isbn"],
                    "title": book["title"],
                    "author": book["author"],
                    "year": book["year"],
                    "total_ratings": total_ratings,
                    "average_rating": round(average_rating,1),
                    "reviews": book_reviews if ratings["ratingcount"] > 0 else []
                },
                message=message,
                error_message=error_message
            )
    except Exception as e:
        logging.error(traceback.format_exc())
        return redirect("/")

@app.route("/api/<string:isbn>",methods=['GET'])
def get_books_by_isbn(isbn):
    try:
        book = db.execute(f"select * from books where isbn = '{isbn}'").fetchone()
        if book == None:
            return make_response(jsonify({
                'status': 404,
                'message': 'No book was found for this isbn number'
            }), 404)
        return jsonify(get_book_data(isbn))
    except Exception as e:
        logging.error(traceback.format_exc())
        return make_response(jsonify({
                'status': 500,
                'message': 'Internal Server Error'
            }), 500)