FROM debian:stretch

RUN apt-get update && apt-get install -y python3-pip

RUN useradd poll

COPY requirements.txt .
RUN pip3 install -r requirements.txt && rm requirements.txt

COPY model.py .
COPY bot.py .

VOLUME /tmp/db

CMD chown -R poll:poll /tmp/db && \
    su poll -c "python3 bot.py"

