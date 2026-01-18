from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import now
import pytz
from django.views.generic import TemplateView

from .models import Message, Mailing, Attempt
from .models import Recipient


class OwnerQuerySetMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


# -------- MESSAGE --------

class MessageListView(LoginRequiredMixin, OwnerQuerySetMixin, ListView):
    model = Message
    template_name = 'mailing/message_list.html'

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    fields = ['subject', 'body']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerQuerySetMixin, UpdateView):
    model = Message
    fields = ['subject', 'body']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message-list')


class MessageDeleteView(LoginRequiredMixin, OwnerQuerySetMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message-list')

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


# -------- MAILING --------

class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = 'mailing/mailing_list.html'

    def get_queryset(self):
        qs = Mailing.objects.filter(owner=self.request.user)
        for m in qs:
            m.update_status()
        return qs


class MailingDetailView(LoginRequiredMixin, OwnerQuerySetMixin, DetailView):
    model = Mailing
    template_name = 'mailing/mailing_detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    fields = ['start_time', 'end_time', 'message', 'recipients']
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerQuerySetMixin, UpdateView):
    model = Mailing
    fields = ['start_time', 'end_time', 'message', 'recipients']
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing-list')

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


class MailingDeleteView(LoginRequiredMixin, OwnerQuerySetMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing-list')

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


# -------- ATTEMPT --------

class AttemptListView(LoginRequiredMixin, ListView):
    model = Attempt
    template_name = 'mailing/attempt_list.html'

    def get_queryset(self):
        return Attempt.objects.filter(mailing__owner=self.request.user)


# -------- MAILING LAUNCH --------

class LaunchMailingView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk, owner=request.user)

        # Приводим текущее время к московскому
        moscow_tz = pytz.timezone("Europe/Moscow")
        now = timezone.now().astimezone(moscow_tz)

        # Приводим даты из формы тоже к московскому времени
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
                        recipient=recipient,  # <-- вот это ключ
                        status='Успешно',
                        server_response='OK'
                    )
                except Exception as e:
                    Attempt.objects.create(
                        mailing=mailing,
                        recipient=recipient,  # <-- и тут не забудь
                        status='Не успешно',
                        server_response=str(e)
                    )
            messages.success(request, 'Рассылка запущена.')
        else:
            # Тут мы должны логировать попытки по каждому получателю
            for recipient in mailing.recipients.all():
                Attempt.objects.create(
                    mailing=mailing,
                    recipient=recipient,  # <-- и тут тоже
                    status='Не успешно',
                    server_response='Рассылка вне допустимого временного интервала'
                )
            messages.error(request, 'Рассылка вне допустимого временного интервала.')

        return redirect('mailing:mailing-detail', pk=pk)


class RecipientListView(LoginRequiredMixin, ListView):
    model = Recipient
    template_name = 'mailing/recipient_list.html'

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, UpdateView):
    model = Recipient
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


class RecipientDeleteView(LoginRequiredMixin, DeleteView):
    model = Recipient
    template_name = 'mailing/recipient_confirm_delete.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def get_queryset(self):
        return Recipient.objects.filter(owner=self.request.user)


class HomeView(LoginRequiredMixin, TemplateView):
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
