from django.contrib import admin
from .models import Recipient, Message, Mailing, Attempt


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Recipient.

    Отображает email, имя и владельца. Позволяет искать по email и имени, фильтровать по владельцу.
    """
    list_display = ('email', 'full_name', 'owner')
    search_fields = ('email', 'full_name')
    list_filter = ('owner',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Message.

    Отображает тему и владельца. Поиск по теме, фильтрация по владельцу.
    """
    list_display = ('subject', 'owner')
    search_fields = ('subject',)
    list_filter = ('owner',)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Mailing.

    Отображает расписание и статус рассылки.
    Фильтрация по статусу и владельцу.
    Выбор получателей через горизонтальный список.
    """
    list_display = ('id', 'start_time', 'end_time', 'status', 'owner')
    list_filter = ('status', 'owner')
    search_fields = ('id',)
    filter_horizontal = ('recipients',)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    """
    Админ-интерфейс для модели Attempt.

    Отображает рассылку, статус попытки и время.
    Фильтрация по статусу и по рассылке.
    """
    list_display = ('mailing', 'status', 'attempt_time')
    list_filter = ('status', 'mailing')
