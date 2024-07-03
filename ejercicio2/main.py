import requests
from celery import Celery

api_key = ''

city = ''

url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}'

app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3, soft_time_limit=5)
def my_task(self):
    try:
        response = requests.get(url)
        data = response.json()
        return data
    except Exception as exc:
        raise self.retry(exc=exc)
