FROM python:3.13
LABEL authors="zakr1"
WORKDIR /app
COPY . .

EXPOSE 3000
EXPOSE 5000


ENTRYPOINT ["python3", "-u", "app.py"]