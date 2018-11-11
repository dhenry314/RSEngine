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
export REDIS_HOST=redis://localhost:6380/0
if ! nc -z localhost 6380 ; then
   /usr/bin/docker run -d -p 6380:6379 redis &
   # wait for redis to start
   echo "Waiting redis to launch on 6380..."
   while ! nc -z localhost 6380; do   
     sleep 1 # wait for 1/10 of the second before check again
   done
   echo "redis launched"
fi
echo "redis is running"
/usr/local/bin/dramatiq app.models.tasks &
/usr/local/bin/flask run --host=0.0.0.0 --port=81
