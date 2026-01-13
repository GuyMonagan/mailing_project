from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Client, Message, Mailing, Attempt


class OwnerQuerySetMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


# -------- CLIENT --------

class ClientListView(LoginRequiredMixin, OwnerQuerySetMixin, ListView):
    model = Client
    template_name = 'mailing/client_list.html'


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('client-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, OwnerQuerySetMixin, UpdateView):
    model = Client
    fields = ['email', 'full_name', 'comment']
    template_name = 'mailing/client_form.html'
    success_url = reverse_lazy('client-list')


class ClientDeleteView(LoginRequiredMixin, OwnerQuerySetMixin, DeleteView):
    model = Client
    template_name = 'mailing/client_confirm_delete.html'
    success_url = reverse_lazy('client-list')


# -------- MESSAGE --------

class MessageListView(LoginRequiredMixin, OwnerQuerySetMixin, ListView):
    model = Message
    template_name = 'mailing/message_list.html'


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    fields = ['subject', 'body']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('message-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, OwnerQuerySetMixin, UpdateView):
    model = Message
    fields = ['subject', 'body']
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('message-list')


class MessageDeleteView(LoginRequiredMixin, OwnerQuerySetMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('message-list')


# -------- MAILING --------

class MailingListView(LoginRequiredMixin, OwnerQuerySetMixin, ListView):
    model = Mailing
    template_name = 'mailing/mailing_list.html'


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
    success_url = reverse_lazy('mailing-list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, OwnerQuerySetMixin, UpdateView):
    model = Mailing
    fields = ['start_time', 'end_time', 'message', 'recipients']
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing-list')


class MailingDeleteView(LoginRequiredMixin, OwnerQuerySetMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing-list')


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
        now = timezone.now()

        if mailing.start_time <= now <= mailing.end_time:
            for client in mailing.recipients.all():
                try:
                    send_mail(
                        mailing.message.subject,
                        mailing.message.body,
                        settings.EMAIL_HOST_USER,
                        [client.email],
                        fail_silently=False,
                    )
                    Attempt.objects.create(
                        mailing=mailing,
                        status='Успешно',
                        server_response='OK'
                    )
                except Exception as e:
                    Attempt.objects.create(
                        mailing=mailing,
                        status='Не успешно',
                        server_response=str(e)
                    )
            messages.success(request, 'Рассылка запущена.')
        else:
            messages.error(request, 'Рассылка вне допустимого временного интервала.')

        return redirect('mailing-detail', pk=pk)
