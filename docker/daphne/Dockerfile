FROM python:3.10

EXPOSE 8001

WORKDIR /app

ENV PYTHONUNBUFFERED 1

RUN pip install cython
RUN git clone https://github.com/taylorvance/hexachromixio.git .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "hexachromixio.asgi:application"]
