# Фудграмм - сайт для лучших рецептов!

## Описание проекта
Проект «Фудграм» — — это веб-платформа, где пользователи могут делиться своими кулинарными шедеврами, находить вдохновение в рецептах других и формировать собственную коллекцию любимых блюд. Проект создан для того, чтобы объединить людей, увлечённых готовкой, и сделать процесс планирования питания простым, удобным и вдохновляющим.

## Запуск backend
1. Вам необходимо клонировать репозиторий с проектом на свой компьютер. В терминале из рабочей директории выполните команду:

```bash
https://github.com/Eralandin/foodgram-st.git
cd foodgram-st/backend
```
2. Следом - установить и активировать виртуальное окружение
```bash
python -m venv env
source ./env/bin/activate
```
3. Затем нужно установить зависимости из файла `requirements.txt`
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```
4. Выполнение миграций:
```bash
python manage.py migrate
```
5. Создание суперпользователя:
```bash
python manage.py createsuperuser
```
6. Загрузка статики:
```bash
python manage.py collectstatic
```

7. И, наконец, запуск сервера:
```bash
python manage.py runserver
```
Для тестирования рекомендую воспользоваться Postman (коллекция запросов имеется в репозитории - postman_collection), этого будет более чем достаточно.

## Полный запуск проекта
1. Создание файла .env в папке проекта:
```.env
SECRET_KEY= ...
ALLOWED_HOSTS=127.0.0.1, localhost
DEBUG=False
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
POSTGRES_DB=foodgram
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
```
2. Создание команды сборки контейнеров
```bash
docker compose up --build
```
3. Выполнение миграций (с другого терминала!):
```bash
docker compose exec backend python manage.py migrate
```
4. Создание суперпользователя:
```bash
docker compose exec backend python manage.py createsureruser
```
5. Загрузка статики:
```bash
docker compose exec backend python manage.py collectstatic
```
