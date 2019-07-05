# coding: utf-8
import os
import urllib.request
import sqlite3
from bs4 import BeautifulSoup
from contextlib import closing
from datetime import datetime
from logging import getLogger

logger = getLogger(__name__)


class Controller(object):

    def __init__(self, app_id, app_name, app_country):

        self.APP_ID = app_id
        self.APP_NAME = app_name
        self.APP_COUNTRY = app_country
        self.DB_PATH = "./database/{}.db".format(self.APP_NAME)
        self.TABLE_NAME = "reviews"
        self.APP_RSS_URL = "http://itunes.apple.com/{}/rss/customerreviews/id={}/sortBy=mostRecent/xml".format(
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
            logger.error("HTTPError: {}".format(err.code))
        except urllib.error.URLError as err:
            logger.error("URLError: {}".format(err.reason))

        soup = BeautifulSoup(body, "html.parser")

        review_dict = []
        for entry in soup.find_all("entry"):
            review_dict.append({
                "updated": entry.find("updated").string,
                "username": entry.find("name").string,
                "entry_id": entry.find("id").string,
                "title": entry.find("title").string,
                "summary": entry.find("content").string,
                "rating": entry.find("im:rating").string,
                "version": entry.find("im:version").string})

        review_dict.reverse()

        return review_dict

    def create_review_database(self):

        try:
            with closing(sqlite3.connect(self.DB_PATH)) as conn:

                connection = conn.cursor()

                create_sql = """CREATE TABLE {} (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    updated VARCHAR(255), username VARCHAR(255), entry_id INT, title TEXT, 
                    summary TEXT, rating INT, version INT) """.format(self.TABLE_NAME)
                logger.info(create_sql)
                connection.execute(create_sql)

                insert_sql = """INSERT INTO {} (updated, username, entry_id, title, summary, 
                    rating, version) VALUES (?,?,?,?,?,?,?)""".format(self.TABLE_NAME)
                logger.info(insert_sql)
                review_values = [tuple(review.values()) for review in self.get_app_reviews()]
                connection.executemany(insert_sql, review_values)

                conn.commit()

        except Exception as e:
            logger.warning(e)

    def update_review_database(self, latest_review_list):

        try:
            with closing(sqlite3.connect(self.DB_PATH)) as conn:

                connection = conn.cursor()

                insert_sql = """INSERT INTO {} (updated, username, entry_id, title, summary, 
                    rating, version) VALUES (?,?,?,?,?,?,?)""".format(self.TABLE_NAME)
                logger.info(insert_sql)
                review_values = [tuple(review.values()) for review in latest_review_list]
                connection.executemany(insert_sql, review_values)

                conn.commit()

        except Exception as e:
            logger.warning(e)

    def check_latest_reviews(self):

        def convert_to_timestamp(string_time=None):
            date = datetime.strptime(string_time, "%Y-%m-%dT%H:%M:%S-07:00")
            return date.timestamp()

        latest_review_list = []

        try:
            with closing(sqlite3.connect(self.DB_PATH)) as conn:

                connection = conn.cursor()

                select_sql = """SELECT updated, entry_id FROM {} ORDER BY id DESC""".format(self.TABLE_NAME)
                logger.indo(select_sql)
                connection.execute(select_sql)
                previous_time_string, previous_entry_id = connection.fetchone()
                previous_timestamp = convert_to_timestamp(previous_time_string)

                for review in self.get_app_reviews():
                    target_timestamp = convert_to_timestamp(review["updated"])
                    target_entry_id = review["entry_id"]

                    if target_timestamp > previous_timestamp and target_entry_id != previous_entry_id:
                        latest_review_list.append(review)

                conn.commit()

        except Exception as e:
            logger.warning(e)

        return latest_review_list


