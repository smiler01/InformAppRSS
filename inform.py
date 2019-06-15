# coding: utf-8
import urllib.request
import json


class SlackInform(object):

    def __init__(self):
        self.WEBHOOK_URL =

    def inform(self):

        obj = {"text": "test"}
        json_data = json.dumps(obj).encode("utf-8")

        request = urllib.request.Request(
            url=self.WEBHOOK_URL,
            data=json_data,
            method="POST",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            print("HTTPError: {}".format(err.code))
        except urllib.error.URLError as err:
            print("URLError: {}".format(err.reason))


if __name__ == "__main__":
    slack_inform = SlackInform()
    slack_inform.inform()
