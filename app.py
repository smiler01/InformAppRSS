# coding: utf-8
import os
import yaml

import controller
import inform
import logger

CONFIG_PATH = "./config.yaml"


def main():

    # read config
    with open(CONFIG_PATH) as file:
        config = yaml.load(stream=file, Loader=yaml.SafeLoader)

    log = logger.Logger(__name__)

    slack_inform = inform.SlackInform(config["slack"][0]["webhook_url"])

    for app in config["application"]:
        app_name = app["name"]
        app_id = app["id"]
        app_country = app["country"]

        database_controller = controller.Controller(app_id, app_name, app_country)
        if not database_controller.check_existence_review_database():
            database_controller.create_review_database()
            log.logger.info("create {} database".format(app_name))

        latest_review_list = database_controller.check_latest_reviews()
        if not latest_review_list:
            log.logger.info("not {} latest reviews".format(app_name))
            continue

        for latest_review in latest_review_list:
            attachments = slack_inform.format_app_review_attachments(app_name, latest_review)
            slack_inform.inform(attachments)

        database_controller.update_review_database(latest_review_list)


if __name__ == "__main__":
    main()
