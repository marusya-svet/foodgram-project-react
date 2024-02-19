# FOODGRAM_PROJECT
Social network for bloggers and cooks!
Here you can post your recipes with photos, follow other cooks, add recipes to the favorites list and to shopping list.
From the shopping list you can download the list of necessary groceries 

### Tecnologies
- Python 3.7
- Django 3.2
- Nginx
- Django REST framework 3.12.4
- Docker
- JSON
- YAML
- PostgreSQL
- Gunicorn
- JWT 
- Postman

### Run project in dev
- Install and activate virtual environment
- Create env-file in backend and infra directories and fill it in like this:
```
POSTGRES_USER=django_user
POSTGRES_PASSWORD=(yourpassword)
POSTGRES_DB=(name)
DB_HOST=(db)
DB_PORT=(5432)
SECRET_KEY=(your secret key)
DEBUG=False
ALLOWED_HOSTS=(your hosts)
``` 
- Create superuser in backend directory 
```
python manage.py createsuperuser
```
- Also in backend directory import ingredients:
```
python manage.py import_json
```
- Download Docker Compose:
```
sudo apt update
sudo apt-get install docker-compose-plugin 
``` 
- Copy docker-compose.yml file to your server and run docker compose on your server 
```
sudo docker compose up -d
``` 

## http://foodgram-svet.hopto.org

## Примеры запросов API

- Add recipe: POST `api/recipes/`
- View recipe: GET `api/recipes/{recipe_id}`

### Author
*Maria Svetlichnaya*
[telegram](https://t.me/msvetlichnaya)
