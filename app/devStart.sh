#! /bin/bash
export FLASK_APP=app/main.py
export FLASK_DEBUG=1
export DB_URI=sqlite://///tmp/RSendpointDev.db
export BASE_URI=http://localhost:81
export HASH_ALGORITHM=md5
export RESOURCE_UNIT=1000
export DATE_UNIT=day
export STATIC_FILES=/tmp/RSEngine/static/
export USER_AGENT=Mozilla/5.0
/usr/local/bin/flask run --host=0.0.0.0 --port=81
