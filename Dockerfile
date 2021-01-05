FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
COPY main.py ./
COPY dev/clean.json ./dev/
COPY dev/msg_codes.json ./dev/



RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./main.py" ]
