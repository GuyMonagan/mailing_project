from django.core.management.base import BaseCommand
from django.utils import timezone
from mailing.models import Mailing, Attempt
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    """
    Команда для отправки всех активных рассылок, у которых текущая дата попадает в указанный интервал.

    Для каждой валидной рассылки отправляет сообщение всем её получателям.
    Записывает успешные и неуспешные попытки в модель Attempt.
    Пропускает рассылки вне временного интервала и логирует ошибки.
    """
    help = 'Отправка всех активных рассылок (если текущая дата в пределах интервала)'

    def handle(self, *args, **kwargs):
        now = timezone.now()

        all_mailings = Mailing.objects.all()

        for mailing in all_mailings:
            if not (mailing.start_time <= now <= mailing.end_time):
                Attempt.objects.create(
                    mailing=mailing,
                    status='Не успешно',
                    server_response='Вне интервала — не отправлено'
                )
                self.stdout.write(self.style.WARNING(
                    f'Пропущено: рассылка {mailing.pk} вне интервала времени.'
                ))
                continue

            # если дошли до сюда — значит можно слать
            for recipient in mailing.recipients.all():
                try:
                    send_mail(
                        mailing.message.subject,
                        mailing.message.body,
                        settings.EMAIL_HOST_USER,
                        [recipient.email],
                        fail_silently=False,
                    )
                    Attempt.objects.create(
                        mailing=mailing,
                        status='Успешно',
                        server_response='OK'
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f"Успешно отправлено: {recipient.email}"
                    ))
                except Exception as e:
                    Attempt.objects.create(
                        mailing=mailing,
                        status='Не успешно',
                        server_response=str(e),
                    )
                    self.stdout.write(self.style.ERROR(
                        f"Ошибка доставки для {recipient.email}: {e}"
                    ))

        self.stdout.write(self.style.SUCCESS("Готово. Все рассылки обработаны."))
