from django.db import models
from django.conf import settings
from django.utils import timezone


class Recipient(models.Model):
    """
    Represents a single recipient in the mailing system.

    Attributes:
        email (str): Unique email address of the recipient.
        full_name (str): Full name of the recipient.
        comment (str, optional): Additional comment or note about the recipient.
        owner (User): The user who owns/created this recipient.

    Permissions:
        - view_all_recipients: Allows viewing recipients created by other users.
    """

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipients'
    )

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    class Meta:
        permissions = [
            ("view_all_recipients", "Может просматривать всех получателей"),
        ]


class Message(models.Model):
    """
    Represents the content of a mass mailing message.

    Attributes:
        subject (str): Subject line of the email.
        body (str): Body text of the message.
        owner (User): The user who created the message.

    Permissions:
        - view_all_messages: Allows viewing messages created by other users.
    """

    subject = models.CharField(max_length=255)
    body = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return self.subject

    class Meta:
        permissions = [
            ("view_all_messages", "Может просматривать все сообщения"),
        ]


class Mailing(models.Model):
    """
    Represents a scheduled mass mailing event.

    Attributes:
        start_time (datetime): When the mailing should begin.
        end_time (datetime): When the mailing should end.
        status (str): Current status of the mailing ("Создана", "Запущена", "Завершена").
        is_active (bool): Whether the mailing is active or disabled.
        message (Message): The message to be sent.
        recipients (QuerySet[Recipient]): Recipients included in the mailing.
        owner (User): The user who created the mailing.

    Methods:
        update_status(): Updates the status field based on the current time.

    Permissions:
        - view_all_mailings: Allows viewing mailings from other users.
        - disable_mailings: Allows deactivating mailings.
    """

    STATUS_CHOICES = [
        ('Создана', 'Создана'),
        ('Запущена', 'Запущена'),
        ('Завершена', 'Завершена'),
    ]

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Создана')

    is_active = models.BooleanField(default=True, verbose_name="Активна")

    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    recipients = models.ManyToManyField(Recipient)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mailings'
    )

    def update_status(self):
        now = timezone.now()

        if now < self.start_time:
            self.status = 'Создана'
        elif self.start_time <= now <= self.end_time:
            self.status = 'Запущена'
        else:
            self.status = 'Завершена'

        self.save()

    def __str__(self):
        return f"{self.message.subject} ({self.status})"

    class Meta:
        permissions = [
            ("view_all_mailings", "Может просматривать все рассылки"),
            ("disable_mailings", "Может отключать рассылки"),
        ]


class Attempt(models.Model):
    """
    Represents a single attempt to send a mailing to a recipient.

    Attributes:
        attempt_time (datetime): Timestamp when the attempt was made.
        status (str): Result of the attempt ("Успешно", "Не успешно").
        server_response (str): Raw response from the email server.
        mailing (Mailing): The associated mailing.
        recipient (Recipient): The recipient the attempt was sent to.
    """
    STATUS_CHOICES = [
        ('Успешно', 'Успешно'),
        ('Не успешно', 'Не успешно'),
    ]

    attempt_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    server_response = models.TextField()
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE)
    recipient = models.ForeignKey('Recipient', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.mailing} — {self.status} at {self.attempt_time}"
