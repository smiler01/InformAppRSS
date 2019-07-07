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

CONFIG_PATH = "./config/.config.yaml"
with open(CONFIG_PATH) as file:
    config = yaml.load(stream=file, Loader=yaml.SafeLoader)
logger.info("Load config parameters")


def main():

    logger.info("START")

    slack_inform = inform.SlackInform(config["slack"]["webhook_url"])
    
    db_host = config["database"]["host"]
    db_user = config["database"]["user"]
    db_pass = config["database"]["password"]
    db_name = config["database"]["name"]
    
    for app in config["application"]:
        app_name = app["name"]
        app_id = app["id"]
        app_country = app["country"]

        logger.info("{} is targetting app.".format(app_name))

        database_controller = controller.Controller(app_id, app_name, app_country,
            db_host, db_user, db_pass, db_name)

        if not database_controller.check_existence_review_table():
            logger.info("{}'s table is not.".format(app_name))
            database_controller.create_review_table()
            logger.info("{}'s table is created now.".format(app_name))
        else:
            logger.info("{}'s table is existence.".format(app_name))        

        database_controller.delete_latest_reviews()

        latest_review_list = database_controller.check_latest_reviews()
        if not latest_review_list:
            logger.info("{} don't have latest reviews.".format(app_name))
            continue

        for latest_review in latest_review_list:
            attachments = slack_inform.format_app_review_attachments(app_name, latest_review)
            slack_inform.inform(attachments)
        logger.info("{}'s latest reviews was notified to slack.".format(app_name))

        database_controller.update_review_table(latest_review_list)
        logger.info("{}'s table has been updated.".format(app_name))

    logger.info("FINISH")


if __name__ == "__main__":
    main()

