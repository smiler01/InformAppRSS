# coding: utf-8
import os
import urllib.request
import sqlite3
from bs4 import BeautifulSoup
from contextlib import closing
from datetime import datetime


class Controller(object):

    def __init__(self, app_id, app_name, app_country):

        self.APP_ID = app_id
        self.APP_NAME = app_name
        self.APP_COUNTRY = app_country
        self.DB_PATH = "./database/{}.db".format(self.APP_NAME)
        self.TABLE_NAME = "reviews"
        self.APP_RSS_URL = "http://itunes.apple.com/{}/rss/customerreviews/id={}/xml".format(
            self.APP_COUNTRY, self.APP_ID)

        if not os.path.exists("./database"):
            os.makedirs("./database")

    def check_existence_review_database(self):

        if os.path.exists(self.DB_PATH):
            return True
        return False

    def get_app_reviews(self):

        request = urllib.request.Request(self.APP_RSS_URL)
        try:
            with urllib.request.urlopen(request) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            print("HTTPError: {}".format(err.code))
        except urllib.error.URLError as err:
            print("URLError: {}".format(err.reason))

        soup = BeautifulSoup(body, "html.parser")

        review_dict = []
        for entry in soup.find_all("entry"):
            review_dict.append({
                "updated": entry.find("updated").string,
                "username": entry.find("name").string,
                "userid": entry.find("id").string,
                "title": entry.find("title").string,
                "summary": entry.find("content").string,
                "rating": entry.find("im:rating").string,
                "version": entry.find("im:version").string})

        return review_dict

    def create_review_database(self):

        try:
            with closing(sqlite3.connect(self.DB_PATH)) as conn:

                connection = conn.cursor()

                create_sql = """CREATE TABLE {} (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    updated VARCHAR(255), username VARCHAR(255), userid INT, title TEXT, 
                    summary TEXT, rating INT, version INT) """.format(self.TABLE_NAME)
                connection.execute(create_sql)

                insert_sql = """INSERT INTO {} (updated, username, userid, title, summary, 
                    rating, version) VALUES (?,?,?,?,?,?,?)""".format(self.TABLE_NAME)
                review_values = [tuple(review.values()) for review in self.get_app_reviews()]
                connection.executemany(insert_sql, review_values)

                conn.commit()

        except Exception as e:
            print(e)

    def update_review_database(self, latest_review_list):

        try:
            with closing(sqlite3.connect(self.DB_PATH)) as conn:

                connection = conn.cursor()

                insert_sql = """INSERT INTO {} (updated, username, userid, title, summary, 
                    rating, version) VALUES (?,?,?,?,?,?,?)""".format(self.TABLE_NAME)
                review_values = [tuple(review.values()) for review in latest_review_list]
                connection.executemany(insert_sql, review_values)

                conn.commit()

        except Exception as e:
            print(e)

    def check_latest_reviews(self):

        def convert_to_timestamp(string_time=None):
            date = datetime.strptime(string_time, "%Y-%m-%dT%H:%M:%S-07:00")
            return date.timestamp()

        try:
            with closing(sqlite3.connect(self.DB_PATH)) as conn:

                connection = conn.cursor()

                select_sql = """SELECT updated FROM {}""".format(self.TABLE_NAME)
                connection.execute(select_sql)
                previous_timestamp = convert_to_timestamp(connection.fetchone()[0])

                latest_review_list = []
                for review in self.get_app_reviews():
                    target_timestamp = convert_to_timestamp(review["updated"])

                    if target_timestamp > previous_timestamp:
                        latest_review_list.append(review)

                conn.commit()

        except Exception as e:
            print(e)

        return latest_review_list
