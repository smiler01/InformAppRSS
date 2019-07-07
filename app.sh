#!/bin/sh
cd /home/ec2-user/reviewbots/appstore
source bin/activate
cd appstore
python app.py
deactivate
cd
