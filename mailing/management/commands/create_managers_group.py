from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class Command(BaseCommand):
    help = "Создает группу Менеджеры с нужными правами"

    def handle(self, *args, **kwargs):
        group, created = Group.objects.get_or_create(name="Менеджеры")

        permissions = Permission.objects.filter(
            codename__in=[
                "view_all_mailings",
                "disable_mailings",
                "view_all_messages",
                "view_all_recipients",
            ]
        )

        group.permissions.set(permissions)
        group.save()

        self.stdout.write(
            self.style.SUCCESS("Группа 'Менеджеры' успешно создана и настроена.")
        )
