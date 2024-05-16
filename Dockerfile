FROM python:3.11

# Install supervisor
RUN apt-get update && apt-get install -y supervisor

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ARG DB_PASSWORD

ARG DB_USERNAME

ARG DB_HOST

ARG DB_PORT

ENV DB_PASSWORD=$DB_PASSWORD

ENV DB_USERNAME=$DB_USERNAME

ENV DB_HOST=$DB_HOST

ENV DB_PORT=$DB_PORT

EXPOSE 80

CMD bash -c "supervisord -c supervisord.conf"