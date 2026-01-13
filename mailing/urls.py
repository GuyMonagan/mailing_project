from django.urls import path
from .views import (
    ClientListView, ClientCreateView, ClientUpdateView, ClientDeleteView,
    MessageListView, MessageCreateView, MessageUpdateView, MessageDeleteView,
    MailingListView, MailingDetailView, MailingCreateView, MailingUpdateView, MailingDeleteView,
    AttemptListView, LaunchMailingView
)

urlpatterns = [
    # CLIENT
    path('clients/', ClientListView.as_view(), name='client-list'),
    path('clients/create/', ClientCreateView.as_view(), name='client-create'),
    path('clients/<int:pk>/update/', ClientUpdateView.as_view(), name='client-update'),
    path('clients/<int:pk>/delete/', ClientDeleteView.as_view(), name='client-delete'),

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

    # ATTEMPTS
    path('attempts/', AttemptListView.as_view(), name='attempt-list'),
]
