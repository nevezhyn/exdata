FROM python:3.6-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt



COPY main.py .
EXPOSE 8181
CMD [ "python", "./main.py" ]
