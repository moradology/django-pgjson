FROM python:2.7

COPY . /opt/pgjsonb
WORKDIR /opt/pgjsonb

RUN pip install -e .
CMD python run_tests.py
