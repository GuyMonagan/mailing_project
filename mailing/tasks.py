from celery import shared_task
from time import sleep

@shared_task
def send_test_email():
    sleep(5)
    print("Письмо отправлено (ну типа)")
