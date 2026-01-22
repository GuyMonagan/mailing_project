from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import pytz
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from .models import Message, Mailing, Attempt
from .models import Recipient

from django.views.decorators.cache import cache_page


class OwnerOrManagerMixin:
    """
    Миксин для ограничения видимости объектов в зависимости от пользователя.

    Менеджеры видят все объекты.
    Обычные пользователи — только свои (по полю owner).
    """
    owner_lookup = "owner"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        # Менеджер — видит всё
        if user.groups.filter(name="Менеджеры").exists():
            return qs

        # Обычный пользователь
        return qs.filter(**{self.owner_lookup: user})


class ManagerForbiddenMixin:
    """
    Миксин, запрещающий доступ менеджерам к определённым вьюхам.

    Если пользователь в группе 'Менеджеры', вызывает handle_no_permission().
    """
    def dispatch(self, request, *args, **kwargs):
        if request.user.groups.filter(name="Менеджеры").exists():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ToggleMailingStatusView(LoginRequiredMixin, View):
    """
    Вьюха для переключения статуса активности рассылки.

    Доступна только менеджерам.
    Меняет поле is_active и выводит сообщение об успешном переключении.
    После действия выполняет редирект.
    """
    def post(self, request, pk):
        user = request.user
        if not user.groups.filter(name="Менеджеры").exists():
            messages.error(request, "Доступ запрещен.")
            return redirect("mailing:mailing-list")

        mailing = get_object_or_404(Mailing, pk=pk)

        mailing.is_active = not mailing.is_active
        mailing.save()

        messages.success(
            request,
            f"Рассылка {'включена' if mailing.is_active else 'отключена'} менеджером."
        )

        next_url = request.GET.get("next") or reverse_lazy("mailing:mailing-list")
        return redirect(next_url)


# -------- MESSAGE --------
@method_decorator(cache_page(60 * 10), name='dispatch')
class MessageListView(LoginRequiredMixin, OwnerOrManagerMixin, ListView):
    """
    Список сообщений рассылки.

    Менеджеры видят все сообщения.
    Обычные пользователи — только свои.
    """
    model = Message
    template_name = 'mailing/message_list.html'


class MessageCreateView(LoginRequiredMixin, CreateView):
    """
    Создание нового сообщения рассылки.

    При сохранении привязывает сообщение к текущему пользователю.
    """
    model = Message
    fields = ['subject', 'body']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerOrManagerMixin, ManagerForbiddenMixin, UpdateView):
    """
    Изменение существующего сообщения рассылки.

    Менеджерам редактирование запрещено.
    Обычные пользователи могут изменять только свои.
    """
    model = Message
    fields = ['subject', 'body']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message-list')


class MessageDeleteView(LoginRequiredMixin, OwnerOrManagerMixin, ManagerForbiddenMixin, DeleteView):
    """
    Удаление сообщения рассылки.

    Менеджерам удаление запрещено.
    Обычные пользователи могут удалять только свои.
    """
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message-list')


# -------- MAILING --------
@method_decorator(cache_page(60 * 10), name='dispatch')
class MailingListView(LoginRequiredMixin, OwnerOrManagerMixin, ListView):
    """
    Список всех рассылок.

    Менеджеры видят все, пользователи — только свои.
    В контекст передаётся флаг is_manager.
    """
    model = Mailing
    template_name = 'mailing/mailing_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_manager'] = user.groups.filter(name="Менеджеры").exists()
        return context


class MailingDetailView(LoginRequiredMixin, OwnerOrManagerMixin, DetailView):
    """
    Детали конкретной рассылки.

    Обновляет статус рассылки при открытии.
    Добавляет флаг is_manager в контекст.
    """
    model = Mailing
    template_name = 'mailing/mailing_detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_manager'] = self.request.user.groups.filter(name="Менеджеры").exists()
        return context


class MailingStatsView(LoginRequiredMixin, DetailView):
    """
    Статистика по конкретной рассылке.

    Отображает статус последней попытки по каждому получателю.
    Считает общее количество успешных и неуспешных попыток.
    Менеджеры видят все, пользователи — только свои рассылки.
    """
    model = Mailing
    template_name = 'mailing/mailing_stats.html'
    context_object_name = 'mailing'

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Менеджеры").exists():
            return Mailing.objects.all()
        return Mailing.objects.filter(owner=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mailing = self.get_object()

        attempts = Attempt.objects.filter(mailing=mailing)

        recipient_status = {}
        for recipient in mailing.recipients.all():
            last_attempt = attempts.filter(recipient=recipient).order_by('-attempt_time').first()
            recipient_status[recipient] = last_attempt.status if last_attempt else '—'

        context['recipient_status'] = recipient_status
        context['success_count'] = attempts.filter(status='Успешно').count()
        context['fail_count'] = attempts.filter(status='Не успешно').count()

        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    """
    Создание новой рассылки.

    Привязывает рассылку к текущему пользователю.
    """
    model = Mailing
    fields = ['start_time', 'end_time', 'message', 'recipients']
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerOrManagerMixin, ManagerForbiddenMixin, UpdateView):
    """
    Редактирование рассылки.

    Менеджерам запрещено редактировать.
    Пользователи могут редактировать только свои рассылки.
    """
    model = Mailing
    fields = ['start_time', 'end_time', 'message', 'recipients']
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing-list')


class MailingDeleteView(LoginRequiredMixin, OwnerOrManagerMixin, ManagerForbiddenMixin, DeleteView):
    """
    Удаление рассылки.

    Менеджерам удаление запрещено.
    Пользователи могут удалять только свои рассылки.
    """
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing-list')


# -------- ATTEMPT --------
@method_decorator(cache_page(15), name='dispatch')
class AttemptListView(LoginRequiredMixin, OwnerOrManagerMixin, ListView):
    """
    Список попыток отправки сообщений (Attempt).

    Показывает только те попытки, которые относятся к рассылкам текущего пользователя.
    Менеджеры видят всё.
    """
    model = Attempt
    template_name = 'mailing/attempt_list.html'
    owner_lookup = "mailing__owner"


# -------- MAILING LAUNCH --------

class LaunchMailingView(LoginRequiredMixin, View):
    """
    Ручной запуск рассылки пользователем.

    - Менеджерам запуск запрещён.
    - Запрещает запуск неактивных рассылок.
    - Отправляет письма получателям, если текущее время в допустимом интервале.
    - Создаёт записи Attempt для всех попыток (успешных и неуспешных).
    """
    def post(self, request, pk):
        user = request.user

        # Выбор queryset в зависимости от роли
        if user.groups.filter(name="Менеджеры").exists():
            qs = Mailing.objects.all()
        else:
            qs = Mailing.objects.filter(owner=user)

        mailing = get_object_or_404(qs, pk=pk)

        # Запрет менеджерам на запуск рассылки
        if user.groups.filter(name="Менеджеры").exists():
            messages.error(request, "Менеджерам запрещено запускать рассылки.")
            return redirect("mailing:mailing-detail", pk=pk)

        # Проверка активности
        if not mailing.is_active:
            messages.error(request, "Рассылка отключена менеджером.")
            return redirect("mailing:mailing-detail", pk=pk)

        # Приводим текущее время к московскому
        moscow_tz = pytz.timezone("Europe/Moscow")
        now = timezone.now().astimezone(moscow_tz)

        start_time = mailing.start_time.astimezone(moscow_tz)
        end_time = mailing.end_time.astimezone(moscow_tz)

        if start_time <= now <= end_time:
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
                        recipient=recipient,
                        status='Успешно',
                        server_response='OK'
                    )
                except Exception as e:
                    Attempt.objects.create(
                        mailing=mailing,
                        recipient=recipient,
                        status='Не успешно',
                        server_response=str(e)
                    )
            messages.success(request, 'Рассылка запущена.')
        else:
            for recipient in mailing.recipients.all():
                Attempt.objects.create(
                    mailing=mailing,
                    recipient=recipient,
                    status='Не успешно',
                    server_response='Рассылка вне допустимого временного интервала'
                )
            messages.error(request, 'Рассылка вне допустимого временного интервала.')

        return redirect('mailing:mailing-detail', pk=pk)


# -------- RECIPIENT --------
@method_decorator(cache_page(60 * 10), name='dispatch')
class RecipientListView(LoginRequiredMixin, OwnerOrManagerMixin, ListView):
    """
    Список получателей рассылки.

    Менеджеры видят всех, пользователи — только своих.
    """
    model = Recipient
    template_name = 'mailing/recipient_list.html'


class RecipientCreateView(LoginRequiredMixin, CreateView):
    """
    Создание нового получателя рассылки.

    Автоматически назначает текущего пользователя как владельца.
    """
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, OwnerOrManagerMixin, ManagerForbiddenMixin, UpdateView):
    """
    Редактирование получателя.

    Менеджерам изменение запрещено.
    Пользователи могут редактировать только своих получателей.
    """
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')


class RecipientDeleteView(LoginRequiredMixin, OwnerOrManagerMixin, ManagerForbiddenMixin, DeleteView):
    """
    Удаление получателя.

    Менеджерам удаление запрещено.
    Пользователи могут удалять только своих.
    """
    model = Recipient
    template_name = 'mailing/recipient_confirm_delete.html'
    success_url = reverse_lazy('mailing:recipient_list')


# ------- OTHER -------
@method_decorator(cache_page(60 * 15), name='dispatch')  # 15 минут
class HomeView(LoginRequiredMixin, TemplateView):
    """
    Домашняя страница пользователя с общей статистикой.

    Показывает количество сообщений, получателей, рассылок и попыток.
    Кэшируется на 15 минут.
    """
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['message_count'] = Message.objects.filter(owner=user).count()
        context['recipient_count'] = Recipient.objects.filter(owner=user).count()
        context['mailing_count'] = Mailing.objects.filter(owner=user).count()
        context['attempt_count'] = Attempt.objects.filter(mailing__owner=user).count()

        context['has_no_messages'] = context['message_count'] == 0
        context['has_no_recipients'] = context['recipient_count'] == 0
        context['has_no_mailings'] = context['mailing_count'] == 0

        return context
