# Foodgram Project [![foodgram_workflow](https://github.com/Simatheone/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)](https://github.com/Simatheone/foodgram-project-react/actions/workflows/yamdb_workflow.yml)

## Оглавление
- [Технологии](#используемые-технологии)
- [Описание проекта](#описание-проекта)
- [Заполнение .env файла](#заполнение-env-файла)
- [Запуск проекта](#запуск-проекта)
<br>

Проект можно посмотреть тут [foodgram](http://foodfoodgram.sytes.net/).

Для входа под админом: 
```
login: admin@admin.ru
password: admin
```

## Используемые технологии

:snake: Python 3.8, :desktop_computer: Django 4.0.4, :arrows_counterclockwise: Django Rest Framework 3.13.1, 

:ship: Docker 3.8, :paintbrush: Nginx 1.21.3, :books: Postgres 13.0, :cloud: YandexCloud (server) 
<hr>

## Описание проекта
Приложение «Продуктовый помощник»: сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации понравившихся авторов.

Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
<hr>

## Заполнение .env файла
В директории infra/ создайте .env файл и укажите значения для переменных окружения:

- SECRET_KEY
- SERVERNAMES
- DB_ENGINE
- DB_NAME
- POSTGRES_USER
- POSTGRES_PASSWORD
- DB_HOST
- DB_PORT
- DEBUG
- CSRF_TRUSTED_ORIGINS

Подсказки по заполнению .env файла можно найти в файлах infra/env.example и infra/env.template.
<hr>

## Запуск проекта
### Для запуска проекта на локальной машине
Необходимо установить Docker на свою рабочую машину. Инструкцию можно найти на [оффициальном сайте](https://docs.docker.com/get-docker/) по Docker.

После установки Docker необходимо:

1. Клонировать репозиторий:
```bash
git clone https://github.com/Simatheone/foodgram-project-react.git
```

2. Перейти в директорию `infra/`:
```bash
cd infra/
```

3. Создать `.env` файл и заполнить его в соответствии с `env.example`, `env.template`.

```bash
touch .env
```

4. В терминали запустить **docker-compose**
```
docker-compose up -d
```

5. Выполнить миграции, сборку статических файлов, заполнение базы исходными ингредиентами, создание супер пользователя:
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
docker-compose exec backend python manage.py csv_upload
docker-compose exec backend python manage.py createsuperuser
```

### Для запуска проекта на сервере
1. Установить [Docker](https://docs.docker.com/engine/install/) на вашу вертуальную машину.

2. Копировать локальные файлы `docker-compose.yml` и `nginx.conf` на виртуальную машину с помощью команд:

```bash
scp docker-compose.yml username@server_ip:/home/<username>/
scp nginx.conf <username>@<server_ip>:/home/<username>/
```
3. Создать `.env` файл и заполнить его в соответствии с `env.example`, `env.template`.

```bash
touch .env
```
4. Запустить проект командой:

```bash
sudo docker-compose up -d
```
5. Выполнить миграции, сборку статических файлов, заполнение базы исходными ингредиентами, создание супер пользователя (пример для Ubuntu):
```bash
sudo docker-compose exec backend python manage.py migrate
sudo docker-compose exec backend python manage.py collectstatic --no-input
sudo docker-compose exec backend python manage.py csv_upload
sudo docker-compose exec backend python manage.py createsuperuser
```
