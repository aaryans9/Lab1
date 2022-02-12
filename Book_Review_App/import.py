import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

def populate_data(db):
    print("Started deleting any existing tables in postgres db....")
    db.execute("DROP TABLE IF EXISTS books cascade")
    db.execute("DROP TABLE IF EXISTS book_reviews cascade")
    db.execute("DROP TABLE IF EXISTS user_accounts cascade")
    print("Successfully deleted existing tables in postgres db....")

    print("Started creating new tables in postgres db....")
    create_tables(db)
    print("Successfully created new tables in postgres db....")

    print("Populating intial data from csv into books table....")
    with open('books.csv') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        for isbn, title, author, year in reader:
            # print(f"INSERT INTO books (isbn, title, author, year) VALUES ({isbn},{title},{author},{year})")
            db.execute(
                f"""
                    INSERT INTO books (isbn, title, author, year) 
                    VALUES ('{isbn}','{title.replace("'","''")}','{author.replace("'","''")}',{year})
                """
            )
            print(f"New book created with title {title}")
    print("Successfully populated intial data from csv into books table....")
    db.commit()

def create_tables(db):
    db.execute("""
        CREATE TABLE user_accounts (
            id SERIAL PRIMARY KEY,
            username VARCHAR (50) UNIQUE NOT NULL,
            password VARCHAR (50) NOT NULL
        );
        """)

    db.execute("""
        CREATE TABLE books (
            id SERIAL PRIMARY KEY,
            isbn  VARCHAR UNIQUE NOT NULL,
            title VARCHAR NOT NULL,
            author VARCHAR NOT NULL,
            year INTEGER NOT NULL
        );
        """)

    db.execute("""
        CREATE TABLE reviews (
            id SERIAL PRIMARY KEY,
            book_id  INTEGER NOT NULL REFERENCES books (id),
            reviewer_id  INTEGER NOT NULL REFERENCES user_accounts (id),
            rating INTEGER NOT NULL,
            review VARCHAR NOT NULL
        );
        """)

if __name__ == "__main__":
    engine = create_engine(os.getenv("DATABASE_URL"))
    db = scoped_session(sessionmaker(bind=engine))
    populate_data(db)
