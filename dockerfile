FROM python:3.14.3-trixie

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

USER kuraweb

CMD [ "gunicorn","-k","geventwebsocket.gunicorn.workers.GeventWebSocketWorker","--timeout","600","--workers","1","--threads","4","--bind","unix:w0.sock","app:create_app()","--access-logfile","logs/access.log","--error-logfile","logs/error.log",]