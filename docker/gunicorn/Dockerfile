FROM python:3.10

EXPOSE 8000

WORKDIR /app

ENV PYTHONUNBUFFERED 1

RUN pip install cython
RUN git clone https://github.com/taylorvance/hexachromixio.git .
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["gunicorn", "-b", "0.0.0.0:8000", "hexachromixio.wsgi:application"]
