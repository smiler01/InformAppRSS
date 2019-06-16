# coding: utf-8
import os
import logging


class Logger(object):

    def __init__(self, target_file_path):

        self.TARGET_FILE_PATH = target_file_path
        self.LOGGER_DIR = "./logger/"
        self.LOGGER_NAME = "info.log"
        self.LOGGER_PATH = "{}{}".format(self.LOGGER_DIR, self.LOGGER_NAME)
        self.LEVEL = logging.DEBUG
        self.FORMATTER = '%(levelname)s : %(asctime)s : %(message)s'

        self.logger = logging.getLogger(self.TARGET_FILE_PATH)

        if not os.path.exists(self.LOGGER_DIR):
            os.makedirs(self.LOGGER_DIR)

        self.logger.setLevel(self.LEVEL)

        # file output
        fh = logging.FileHandler(self.LOGGER_PATH)

        # console output
        sh = logging.StreamHandler()

        # set formatter
        formatter = logging.Formatter(self.FORMATTER)
        fh.setFormatter(formatter)
        sh.setFormatter(formatter)

        # add handler
        self.logger.addHandler(fh)
        self.logger.addHandler(sh)
