from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import ListView, View
from users.forms import RegisterForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


def register(request):
    if request.user.is_authenticated:
        return redirect('mailing:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)

            subject = 'Подтверждение регистрации'
            message = render_to_string(
                'users/activation_email.html',
                {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(
                        force_bytes(user.pk)
                    ),
                    'token': default_token_generator.make_token(user),
                },
            )

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

            return render(
                request,
                'users/registration_done.html',
                {'email': user.email},
            )
    else:
        form = RegisterForm()

    return render(
        request,
        'users/register.html',
        {'form': form},
    )


def activate(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        login(request, user)

        messages.success(
            request,
            'Email успешно подтверждён. Вы вошли в аккаунт.'
        )

        return redirect('mailing:home')

    return HttpResponse(
        'Ссылка подтверждения недействительна или устарела.',
        status=400,
    )

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'mailing/user_list.html'
    context_object_name = 'users'

    def test_func(self):
        return is_manager(self.request.user)

class UserBlockView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_manager(self.request.user)

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)

        if user.is_superuser:
            messages.error(
                request,
                'Суперпользователя нельзя заблокировать.'
            )
        else:
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


