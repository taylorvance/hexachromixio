FROM python:3.10

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE hexachromixio.settings

RUN pip install cython

WORKDIR /app

RUN pip install gunicorn daphne

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput
