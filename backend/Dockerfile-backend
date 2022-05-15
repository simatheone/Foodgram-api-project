FROM python:3.7-slim
WORKDIR /foodgram_backend
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "foodgam.wsgi:application", "--bind", "0:8000"]