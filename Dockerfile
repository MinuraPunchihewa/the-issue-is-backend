FROM python:3.8

ENV SECRET_KEY=dev
ENV JWT_SECRET_KEY=dev

ADD . .

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip3 install -U flask-cors

EXPOSE 8080

CMD [ "python", "run.py" ]