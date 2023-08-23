FROM python:3.11-slim-bullseye

WORKDIR /usr/src/app

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV EPIDOC_FILES_DIR="./epidoc_files"

CMD ["/bin/sh", "start.sh"]
