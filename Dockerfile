FROM tiangolo/uwsgi-nginx-flask:python3.6

COPY ./app /app
COPY ./app/data /app/data

WORKDIR /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt \
    && pip install -U 'dramatiq[redis,watch]'

VOLUME /app/data

