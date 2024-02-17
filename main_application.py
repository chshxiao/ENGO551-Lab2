import os
import requests
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker, scoped_session
from flask import Flask, render_template, request, session, redirect, jsonify
from flask_session import Session
from user import *

users = []
users.append(User(user_id="Roy", password="1111"))

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# store the user's information
user_id = []


# login page
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_id.append(request.form.get("user_id"))
        password = request.form.get("user_password")

        user = db.execute(text("""SELECT * FROM users WHERE user_id = :user_id"""), {"user_id": user_id[0]}).fetchone()

        if user and user.password == password:
            session['user_id'] = user.user_id
            return redirect("/book")
        return render_template("index.html", message="wrong id or password")
    return render_template("index.html")


# register new account page
@app.route("/register")
def register():
    return render_template("register.html")


# register succeed page
@app.route("/register/result", methods=["POST"])
def register_result():

    new_id = request.form.get("user_id")
    new_password = request.form.get("user_password")

    # check if the user id exist in our database
    duplicate = db.execute(text("SELECT * FROM users WHERE user_id = :new_id"), {"new_id": new_id}).fetchone()

    # this is a new account
    if duplicate is None:
        db.execute(text("""INSERT INTO users (user_id, password)
                            VALUES(:new_id, :new_password)"""),
                   {"new_id": new_id, "new_password": new_password})
        db.commit()

        return render_template("registerresult.html")

    # the account already exists
    else:
        return render_template("register.html", message="The account already exist")


# logout page
@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.pop('user_id')
    user_id.clear()
    return redirect("/")


# book searching page
@app.route("/book", methods=['GET', 'POST'])
def main_page():
    search_result = []

    if request.method == "GET":
        return render_template("mainpage.html", book=search_result)

    else:
        input_type = request.form.get("type")
        input_value = "%" + request.form.get("value") + "%"

        if input_type == "author":
            search_result = db.execute(text("""SELECT * FROM books
                                                    WHERE author_id IN
                                                    (SELECT id FROM authors
                                                    WHERE name LIKE :name)"""), {"name": input_value}).fetchall()
        else:
            search_result = db.execute(text("SELECT * FROM books "
                                            "WHERE " + input_type + " LIKE :input_value"),
                                       {"input_value": input_value}).fetchall()

        if len(search_result) == 0:
            return render_template("error.html", message="Nothing Match")
        else:
            return render_template("mainpage.html", books=search_result)


# book detail page
@app.route("/book/<string:isbn>/")
def book_detail(isbn):
    local_detail = db.execute(text("""SELECT b.isbn, b.title, au.name, b.year
                                    FROM books AS b, authors AS au
                                    WHERE b.isbn =:isbn
                                    AND b.author_id = au.id"""),
                              {"isbn": isbn}).fetchone()

    reviews = db.execute(text("""SELECT b.isbn, r.review, r.user_id
                                    FROM books AS b, reviews AS r
                                    WHERE b.isbn = :isbn
                                    AND r.isbn = b.isbn"""),
                         {"isbn": isbn}).fetchall()

    if len(local_detail) == 0:
        return render_template("error.html", message="Cannot find the details of the book")
    else:
        # get the isbn and find the book from api
        api_detail = extract_rating_from_api(isbn)

        # get the real date
        final_publish_date = coalesce_publish_date(local_detail.year, api_detail['publishedDate'])

        return render_template("detail.html", detail=local_detail, reviews=reviews,
                               api_detail=api_detail, published_date=final_publish_date)


# book detail api page
@app.route("/api/book/<string:isbn>/")
def book_detail_api(isbn):
    # validate the isbn
    detail = db.execute(text("""SELECT b.isbn, b.title, au.name, b.year
                                FROM books AS b, authors AS au
                                WHERE b.isbn =:isbn AND b.author_id = au.id"""),
                        {"isbn": isbn}).fetchone()

    reviews = db.execute(text("""SELECT b.isbn, r.review
                                    FROM books AS b, reviews AS r
                                    WHERE b.isbn = :isbn
                                    AND r.isbn = b.isbn"""),
                         {"isbn": isbn}).fetchall()

    if detail is None:
        return jsonify({"Error": "Invalid ISBN"}), 404

    # get the isbn and find the book from api
    api_detail = extract_rating_from_api(isbn)
    print(reviews)

    return jsonify({
        "title": detail.title,
        "author": detail.name,
        "publishedDate": api_detail["publishedDate"],
        "ISBN10": api_detail["isbn10"],
        "ISBN13": api_detail["isbn13"],
        "averageRating": api_detail["averageRating"],
        "reviewCount": len(reviews)
    })


# write a review
@app.route("/book/<string:isbn>/writereview/")
def write_review(isbn):
    # check if the user have already written a review for the book
    review_record = db.execute(text("""SELECT * FROM reviews
                                        WHERE user_id = :user_id AND isbn = :isbn"""),
                               {"user_id": user_id[0], "isbn": isbn}).fetchone()

    print(review_record)

    if review_record is not None:
        return render_template("error.html", message="You have review on this book")

    return render_template("writereview.html", isbn=isbn)


# load the review
@app.route("/reviewupload/<string:isbn>/", methods=['POST'])
def upload_review(isbn):
    # get the rating and the text review
    rating = request.form.get('rating')
    review = request.form.get('review')

    print(isbn)

    # insert the rating and review to reviews table in database
    db.execute(text("""INSERT INTO reviews (user_id, isbn, review, rating)
                        VALUES(:user_id, :isbn, :review, :rating)"""),
               {"user_id": user_id[0], "isbn": isbn, "review": review, "rating": rating})
    db.commit()

    return render_template("review.html")


def extract_rating_from_api(isbn):
    # get the isbn and find the book from api
    param_value = "isbn:" + isbn
    api_detail_ls = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": param_value})

    api_detail_js = api_detail_ls.json()
    publish_date = api_detail_js["items"][0]["volumeInfo"]['publishedDate']  # published date
    isbn_13 = api_detail_js["items"][0]["volumeInfo"]["industryIdentifiers"][0]["identifier"]
    isbn_10 = api_detail_js["items"][0]["volumeInfo"]["industryIdentifiers"][1]["identifier"]

    # average rating and review count might not be applicable to some books
    if "averageRating" in api_detail_js["items"][0]["volumeInfo"].keys():
        avg_rating = api_detail_js["items"][0]["volumeInfo"]["averageRating"]
    else:
        avg_rating = ""

    # return a dictionary
    res = {"isbn10": isbn_10, "isbn13": isbn_13, "publishedDate": publish_date, "averageRating": avg_rating}

    return res


def coalesce_publish_date(local_date, api_date):
    if api_date == "":
        return local_date
    else:
        return api_date
