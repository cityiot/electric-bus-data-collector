FROM python:3.7.3

RUN mkdir -p /electric-bus/src
RUN mkdir -p /electric-bus/conf

COPY requirements.txt /electric-bus/requirements.txt

RUN pip install -r /electric-bus/requirements.txt

COPY src/*.py /electric-bus/src/
COPY conf/*.json /electric-bus/conf/
COPY subscription.json /electric-bus/

WORKDIR /electric-bus

CMD [ "python3", "-u", "src/main.py" ]
