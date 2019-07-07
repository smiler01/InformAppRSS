# -*- coding: utf-8 -*- 
import os
import urllib.request
import pymysql
from bs4 import BeautifulSoup
from contextlib import closing
from datetime import datetime
from logging import getLogger

logger = getLogger(__name__)


class Controller(object):

    def __init__(self, app_id, app_name, app_country, db_host, db_user, db_password, db_name):

        # App info
        self.APP_ID = app_id
        self.APP_NAME = app_name
        self.APP_COUNTRY = app_country
        self.APP_RSS_URL = "http://itunes.apple.com/{}/rss/customerreviews/id={}/sortBy=mostRecent/xml".format(
            self.APP_COUNTRY, self.APP_ID)

        # DB info
        self.DB_HOST = db_host 
        self.DB_USER = db_user
        self.DB_PASSWORD = db_password 
        self.DB_NAME = db_name 
        self.TABLE_NAME = "{}_reviews".format(self.APP_NAME)
        self.CHARSET = "utf8mb4"
        
    def check_existence_review_table(self):

        try: 
            with closing(pymysql.connect(self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME, charset=self.CHARSET)) as conn:
                connection = conn.cursor()
                select_sql = """SELECT 1 FROM `{}` LIMIT 1;""".format(self.TABLE_NAME)
                logger.info(select_sql)
                connection.execute(select_sql)
                conn.commit()
        except Exception as e:
            logger.warning(e)
            return False            
        return True

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
                "updated": entry.find("updated").text,
                "username": entry.find("name").text,
                "entry_id": entry.find("id").text,
                "title": entry.find("title").text,
                "summary": entry.find("content").text,
                "rating": int(entry.find("im:rating").text),
                "version": entry.find("im:version").text})

        review_dict.reverse()

        return review_dict

    def create_review_table(self):

        try:
            with closing(pymysql.connect(self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME, charset=self.CHARSET)) as conn:

                connection = conn.cursor()

                create_sql = """CREATE TABLE `{}` (`id` INT PRIMARY KEY NOT NULL AUTO_INCREMENT, `updated` VARCHAR(255), `username` VARCHAR(255), `entry_id` VARCHAR(255), `title` TEXT, `summary` TEXT, `rating` INT, `version` VARCHAR(255)) ;""".format(self.TABLE_NAME)
                logger.info(create_sql)
                connection.execute(create_sql)
 
                alter_sql = """ALTER TABLE `{}` CONVERT TO CHARACTER SET `{}`""".format(self.TABLE_NAME, self.CHARSET)
                logger.info(alter_sql)
                connection.execute(alter_sql)                

                insert_sql = """INSERT INTO `{}` (`updated`, `username`, `entry_id`, `title`, `summary`, `rating`, `version`) VALUES (%s,%s,%s,%s,%s,%s,%s);""".format(self.TABLE_NAME)
                logger.info(insert_sql)
                review_values = [tuple(review.values()) for review in self.get_app_reviews()]
                connection.executemany(insert_sql, review_values)

                conn.commit()

        except Exception as e:
            logger.warning(e)

    def update_review_table(self, latest_review_list):

        try:
            with closing(pymysql.connect(self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME, charset=self.CHARSET)) as conn:

                connection = conn.cursor()

                insert_sql = """INSERT INTO `{}` (`updated`, `username`, `entry_id`, `title`, `summary`, `rating`, `version`) VALUES (%s,%s,%s,%s,%s,%s,%s);""".format(self.TABLE_NAME)
                logger.info(insert_sql)
                review_values = [tuple(review.values()) for review in latest_review_list]
                connection.executemany(insert_sql, review_values)

                conn.commit()

        except Exception as e:
            print(e)
            logger.warning(e)

    def check_latest_reviews(self):

        def convert_to_timestamp(string_time=None):
            date = datetime.strptime(string_time, "%Y-%m-%dT%H:%M:%S-07:00")
            return date.timestamp()

        latest_review_list = []

        try:
            with closing(pymysql.connect(self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME, charset=self.CHARSET)) as conn:

                connection = conn.cursor()

                select_sql = """SELECT `updated`, `entry_id` FROM {} ORDER BY `id` DESC;""".format(self.TABLE_NAME)
                logger.info(select_sql)
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
    
    def delete_latest_reviews(self, num=1):

        try:
            with closing(pymysql.connect(self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME, charset=self.CHARSET)) as conn:

                connection = conn.cursor()

                delete_sql = """DELETE FROM {} ORDER BY `id` DESC LIMIT {};""".format(self.TABLE_NAME, num)
                logger.info(delete_sql)
                connection.execute(delete_sql)

                conn.commit()
        
        except Exception as e:
            logger.warning(e)

