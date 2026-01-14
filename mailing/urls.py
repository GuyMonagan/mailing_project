from django.urls import path
from django.views.generic import TemplateView
from . import views
from .views import (
    MessageListView, MessageCreateView, MessageUpdateView, MessageDeleteView,
    MailingListView, MailingDetailView, MailingCreateView, MailingUpdateView, MailingDeleteView,
    AttemptListView, LaunchMailingView
)

from .views import (
    RecipientListView,
    RecipientCreateView,
    RecipientUpdateView,
    RecipientDeleteView,
)

app_name = 'mailing'

urlpatterns = [

    path('', TemplateView.as_view(template_name="home.html"), name='home'),

    # RECIPIENTS
    path('recipients/', RecipientListView.as_view(), name='recipient_list'),
    path('recipients/create/', RecipientCreateView.as_view(), name='recipient_create'),
    path('recipients/<int:pk>/update/', RecipientUpdateView.as_view(), name='recipient_update'),
    path('recipients/<int:pk>/delete/', RecipientDeleteView.as_view(), name='recipient_delete'),


    # MESSAGE
    path('messages/', MessageListView.as_view(), name='message-list'),
    path('messages/create/', MessageCreateView.as_view(), name='message-create'),
    path('messages/<int:pk>/update/', MessageUpdateView.as_view(), name='message-update'),
    path('messages/<int:pk>/delete/', MessageDeleteView.as_view(), name='message-delete'),


    # MAILING
    path('mailings/', MailingListView.as_view(), name='mailing-list'),
    path('mailings/create/', MailingCreateView.as_view(), name='mailing-create'),
    path('mailings/<int:pk>/', MailingDetailView.as_view(), name='mailing-detail'),
    path('mailings/<int:pk>/update/', MailingUpdateView.as_view(), name='mailing-update'),
    path('mailings/<int:pk>/delete/', MailingDeleteView.as_view(), name='mailing-delete'),
    path('mailings/<int:pk>/launch/', LaunchMailingView.as_view(), name='mailing-launch'),

    path('mailings/', MailingListView.as_view(), name='mailing-list'),

    path('<int:pk>/', views.MailingDetailView.as_view(), name='mailing-detail'),
    path('<int:pk>/launch/', LaunchMailingView.as_view(), name='mailing-launch'),

    # ATTEMPTS
    path('attempts/', AttemptListView.as_view(), name='attempt-list'),
]
