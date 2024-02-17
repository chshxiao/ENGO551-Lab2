import os
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy.orm import sessionmaker, scoped_session


engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():

    # create authors table
    db.execute(text("""CREATE TABLE Authors (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR NOT NULL);"""))

    # create books table
    db.execute(text("""CREATE TABLE Books (
                        isbn VARCHAR PRIMARY KEY,
                        title VARCHAR NOT NULL,
                        year INT NOT NULL,
                        author_id INT NOT NULL);"""))

    # create records table
    db.execute(text("""CREATE TABLE Records (
                        isbn VARCHAR PRIMARY KEY,
                        title VARCHAR NOT NULL,
                        year INT NOT NULL,
                        author_name VARCHAR);"""))

    # create users table
    db.execute(text("""CREATE TABLE users (
                        user_id VARCHAR PRIMARY KEY,
                        password VARCHAR NOT NULL);"""))

    # create reviews table
    db.execute(text("""CREATE TABLE reviews (
                        user_id VARCHAR NOT NULL,
                        isbn VARCHAR NOT NULL,
                        review VARCHAR NOT NULL,
                        rating INT NOT NULL);"""))
    db.commit()


if __name__ == "__main__":
    main()