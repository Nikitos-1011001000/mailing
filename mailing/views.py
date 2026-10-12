from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.views.decorators.cache import cache_page, cache_control
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from mailing.forms import MailingForm, MessageForm, RecipientForm
from mailing.models import Mailing, Message, Recipient
from mailing.services import send_mailing

User = get_user_model()

def is_manager(user):
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(name='Менеджеры').exists()
        )
    )

def is_owner_or_manager(user, obj):
    return obj.user == user or is_manager(user)

class OwnerOrManagerQuerysetMixin:
    """
    Ограничивает queryset объектами текущего пользователя.
    """

    def get_queryset(self):
        queryset = self.model.objects.all()

        if is_manager(self.request.user):
            return queryset

        return queryset.filter(user=self.request.user)

class OwnerOnlyEditMixin:
    """
    Редактировать и удалять может только владелец.
    Менеджер может только просматривать.
    """

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if obj.user != self.request.user:
            raise PermissionDenied

        return obj


class HomeView(TemplateView):
    template_name = 'mailing/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cache_key = f'home_stats_{user.pk}'

        stats = cache.get(cache_key)

        if stats is None:
            now = timezone.now()

            stats = {
                'mailings_count': Mailing.objects.filter(
                    user=user,
                ).count(),
                'active_mailings_count': Mailing.objects.filter(
                    user=user,
                    start_time__lte=now,
                    end_time__gte=now,
                    status=Mailing.STATUS_RUNNING,
                ).count(),
                'recipients_count': Recipient.objects.filter(
                    user=user,
                ).count(),
            }

            cache.set(cache_key, stats, 60 * 5)

        context.update(stats)
        return context

@method_decorator(cache_page(60 * 5), name='dispatch')
class PublicAboutView(TemplateView):
    template_name = 'mailing/about.html'

class RecipientListView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    ListView,
):
    model = Recipient
    template_name = 'mailing/recipient_list.html'
    context_object_name = 'recipients'


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = Recipient
    form_class = RecipientForm
    template_name = 'mailing/form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class RecipientUpdateView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    OwnerOnlyEditMixin,
    UpdateView,
):
    model = Recipient
    form_class = RecipientForm
    template_name = 'mailing/form.html'
    success_url = reverse_lazy('mailing:recipient_list')


class RecipientDeleteView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    OwnerOnlyEditMixin,
    DeleteView,
):
    model = Recipient
    template_name = 'mailing/confirm_delete.html'
    success_url = reverse_lazy('mailing:recipient_list')


class MessageListView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    ListView,
):
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'messages'


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/form.html'
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class MessageUpdateView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    OwnerOnlyEditMixin,
    UpdateView,
):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/form.html'
    success_url = reverse_lazy('mailing:message_list')


class MessageDeleteView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    OwnerOnlyEditMixin,
    DeleteView,
):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')


class MailingListView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    ListView,
):
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        mailings = super().get_queryset().select_related(
            'message',
        ).prefetch_related('recipients')

        for mailing in mailings:
            mailing.update_status()

        return mailings


class MailingDetailView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    DetailView,
):
    model = Mailing
    template_name = 'mailing/mailing_detail.html'
    context_object_name = 'mailing'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class MailingUpdateView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    OwnerOnlyEditMixin,
    UpdateView,
):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/form.html'
    success_url = reverse_lazy('mailing:mailing_list')


class MailingDeleteView(
    LoginRequiredMixin,
    OwnerOrManagerQuerysetMixin,
    OwnerOnlyEditMixin,
    DeleteView,
):
    model = Mailing
    template_name = 'mailing/confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing_list')


class MailingSendView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mailing = get_object_or_404(
            Mailing,
            pk=pk,
            user=request.user,
        )

        try:
            results = send_mailing(mailing)

            messages.success(
                request,
                'Рассылка выполнена. '
                f'Успешно: {results["success"]}; '
                f'ошибок: {results["failed"]}.'
            )

        except ValueError as error:
            messages.error(request, str(error))

        return redirect('mailing:mailing_detail', pk=mailing.pk)

class UserListView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    ListView,
):
    model = User
    template_name = "mailing/user_list.html"
    context_object_name = "users"

    def test_func(self):
        return is_manager(self.request.user)


class UserBlockView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    View,
):
    """
    Блокирует или разблокирует пользователя.
    Доступно только менеджеру.
    """

    def test_func(self):
        return is_manager(self.request.user)

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        if user.is_superuser:
            messages.error(
                request,
                'Суперпользователя нельзя заблокировать.'
            )
            return redirect('mailing:user_list')

        user.is_active = not user.is_active
        user.save(
            update_fields=['is_active'],
        )

        if user.is_active:
            messages.success(
                request,
                f'Пользователь {user.username} разблокирован.'
            )
        else:
            messages.success(
                request,
                f'Пользователь {user.username} заблокирован.'
            )

        return redirect('mailing:user_list')


class MailingToggleActiveView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    View,
):
    """
    Включает или отключает рассылку.
    Доступно только менеджеру.
    """

    def test_func(self):
        return is_manager(self.request.user)

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)

        mailing.is_active = not mailing.is_active
        mailing.save(
            update_fields=['is_active'],
        )

        if mailing.is_active:
            messages.success(
                request,
                'Рассылка включена.'
            )
        else:
            messages.success(
                request,
                'Рассылка отключена.'
            )

        return redirect('mailing:mailing_detail', pk=mailing.pk)

@login_required
def user_stats(request):
    cache_key = f'user_stats_{request.user.pk}'

    stats = cache.get(cache_key)

    if stats is None:
        aggregated = Mailing.objects.filter(
            user=request.user,
        ).aggregate(
            total_sent=Sum('sent_count'),
            total_failed=Sum('failed_count'),
        )

        stats = {
            'total_sent': aggregated['total_sent'] or 0,
            'total_failed': aggregated['total_failed'] or 0,
        }

        cache.set(cache_key, stats, 60 * 5)

    context = {
        'total_sent': stats['total_sent'],
        'total_failed': stats['total_failed'],
    }

    return render(request, 'mailing/user_stats.html', context)