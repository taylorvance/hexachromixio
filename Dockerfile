FROM python:3.10

ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install requirements before cloning the repo, to speed up builds.
# Requirements don't change as frequently as the rest of the source, and pip install is the slowest step.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Copy the local repo and clone it.
#COPY . /tmp/repo
#RUN git clone /tmp/repo . && rm -rf /tmp/repo
# The above isn't working so I'll do it the dumb way.
COPY . .

RUN python manage.py collectstatic --noinput
