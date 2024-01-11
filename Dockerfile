FROM python:3.10

WORKDIR /app

ENV PYTHONUNBUFFERED 1

RUN git clone https://github.com/taylorvance/hexachromixio.git .
RUN pip install --no-cache-dir -r requirements.txt

RUN python manage.py collectstatic --noinput
