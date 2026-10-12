from django.urls import path
from .views import PublicAboutView
from mailing import views

app_name = 'mailing'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),

    path(
        'recipients/',
        views.RecipientListView.as_view(),
        name='recipient_list',
    ),
    path(
        'recipients/create/',
        views.RecipientCreateView.as_view(),
        name='recipient_create',
    ),
    path(
        'recipients/<int:pk>/edit/',
        views.RecipientUpdateView.as_view(),
        name='recipient_update',
    ),
    path(
        'recipients/<int:pk>/delete/',
        views.RecipientDeleteView.as_view(),
        name='recipient_delete',
    ),

    path(
        'messages/',
        views.MessageListView.as_view(),
        name='message_list',
    ),
    path(
        'messages/create/',
        views.MessageCreateView.as_view(),
        name='message_create',
    ),
    path(
        'messages/<int:pk>/edit/',
        views.MessageUpdateView.as_view(),
        name='message_update',
    ),
    path(
        'messages/<int:pk>/delete/',
        views.MessageDeleteView.as_view(),
        name='message_delete',
    ),

    path(
        'mailings/',
        views.MailingListView.as_view(),
        name='mailing_list',
    ),
    path(
        'mailings/create/',
        views.MailingCreateView.as_view(),
        name='mailing_create',
    ),
    path(
        'mailings/<int:pk>/',
        views.MailingDetailView.as_view(),
        name='mailing_detail',
    ),
    path(
        'mailings/<int:pk>/edit/',
        views.MailingUpdateView.as_view(),
        name='mailing_update',
    ),
    path(
        'mailings/<int:pk>/delete/',
        views.MailingDeleteView.as_view(),
        name='mailing_delete',
    ),
    path(
        'mailings/<int:pk>/send/',
        views.MailingSendView.as_view(),
        name='mailing_send',
    ),
    path(
        'stats/',
        views.user_stats,
        name='user_stats',
    ),
    path(
        'users/',
        views.UserListView.as_view(),
        name='user_list',
    ),
    path(
        'users/<int:pk>/block/',
        views.UserBlockView.as_view(),
        name='user_block',
    ),
    path(
        'mailing/<int:pk>/toggle-active/',
        views.MailingToggleActiveView.as_view(),
        name='mailing_toggle_active',
    ),
    path('about/', PublicAboutView.as_view(), name='about'),
    path('', views.UserListView.as_view(), name='user-list'),
]