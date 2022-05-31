FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./

COPY main.py ./

COPY src/cfg.py ./src/
COPY src/etc.py ./src/
COPY src/mqtt.py ./src/
COPY src/oko.py ./src/

COPY dev/clean.json ./dev/
COPY dev/msg_codes.json ./dev/



RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./main.py" ]
