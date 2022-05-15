FROM python:3.8-slim
WORKDIR /foodgram_backend
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip && \
    pip3 install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]