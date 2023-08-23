FROM python:3.11

WORKDIR /usr/src/app

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# We're putting the Dockerfile in the root
# directory instead of the in the web app directory
# so that we can access epidoc-files/ and the taxonomies file
COPY ./epidoc-files ./epidoc_files
COPY ./include_taxonomies.xml ./include_taxonomies.xml

COPY ./db ./db
COPY ./iip_search ./iip_search
COPY ./pleiades_cache ./pleiades_cache
COPY ./alembic.ini ./alembic.ini
COPY ./ingest_inscriptions.py ./ingest_inscriptions.py

ENV EPIDOC_FILES_DIR="./epidoc_files"

ENV DB_URL=$DATABASE_URL

RUN alembic upgrade head
RUN python ./ingest_inscriptions.py

CMD ["uvicorn", "iip_search.app:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
