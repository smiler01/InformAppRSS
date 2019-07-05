# coding: utf-8
import os
import yaml
import logging.config

import controller
import inform

LOG_DIR_PATH = "./log"
if not os.path.exists(LOG_DIR_PATH):
    os.makedirs(LOG_DIR_PATH)

CONFIG_LOGGING = "./config/logging.conf"
logging.config.fileConfig(CONFIG_LOGGING)
logger = logging.getLogger()

CONFIG_PATH = "./config/config.yaml"
with open(CONFIG_PATH) as file:
    config = yaml.load(stream=file, Loader=yaml.SafeLoader)
logger.info("Load config parameters")


def main():

    logger.info("START")

    slack_inform = inform.SlackInform(config["slack"][0]["webhook_url"])

    for app in config["application"]:
        app_name = app["name"]
        app_id = app["id"]
        app_country = app["country"]

        database_controller = controller.Controller(app_id, app_name, app_country)
        if not database_controller.check_existence_review_database():
            database_controller.create_review_database()
            logger.info("create {} database".format(app_name))

        latest_review_list = database_controller.check_latest_reviews()
        if not latest_review_list:
            logger.info("not {} latest reviews".format(app_name))
            continue

        for latest_review in latest_review_list:
            attachments = slack_inform.format_app_review_attachments(app_name, latest_review)
            slack_inform.inform(attachments)

        database_controller.update_review_database(latest_review_list)

    logger.info("FINISH")


if __name__ == "__main__":
    main()
