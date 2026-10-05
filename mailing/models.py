from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Recipient(models.Model):
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name='Ф. И. О.',
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий',
    )

    class Meta:
        verbose_name = 'Получатель рассылки'
        verbose_name_plural = 'Получатели рассылки'
        ordering = ('full_name',)

    def __str__(self):
        return f'{self.full_name} <{self.email}>'


class Message(models.Model):
    subject = models.CharField(
        max_length=255,
        verbose_name='Тема письма',
    )
    body = models.TextField(
        verbose_name='Тело письма',
    )

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ('subject',)

    def __str__(self):
        return self.subject


class Mailing(models.Model):
    STATUS_CREATED = 'created'
    STATUS_RUNNING = 'running'
    STATUS_FINISHED = 'finished'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_RUNNING, 'Запущена'),
        (STATUS_FINISHED, 'Завершена'),
    ]

    start_time = models.DateTimeField(
        verbose_name='Дата и время начала отправки',
    )
    end_time = models.DateTimeField(
        verbose_name='Дата и время окончания отправки',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name='Статус',
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.PROTECT,
        related_name='mailings',
        verbose_name='Сообщение',
    )
    recipients = models.ManyToManyField(
        Recipient,
        related_name='mailings',
        verbose_name='Получатели',
    )

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ('-start_time',)

    def __str__(self):
        return f'Рассылка №{self.pk}: {self.message.subject}'

    def clean(self):
        """Проверяет даты перед сохранением формы."""
        now = timezone.now()

        if self.start_time and self.start_time < now:
            raise ValidationError({
                'start_time': (
                    'Дата и время начала рассылки '
                    'не могут быть в прошлом.'
                )
            })

        if (
                self.start_time
                and self.end_time
                and self.start_time >= self.end_time
        ):
            raise ValidationError({
                'end_time': (
                    'Дата окончания должна быть позже '
                    'даты начала рассылки.'
                )
            })

    def update_status(self):
        """Пересчитывает и при необходимости сохраняет статус."""
        now = timezone.now()

        if now < self.start_time:
            new_status = self.STATUS_CREATED
        elif self.start_time <= now <= self.end_time:
            new_status = self.STATUS_RUNNING
        else:
            new_status = self.STATUS_FINISHED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])

        return self.status


class MailingAttempt(models.Model):
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Успешно'),
        (STATUS_FAILED, 'Не успешно'),
    ]

    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время попытки',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        verbose_name='Статус',
    )
    server_response = models.TextField(
        blank=True,
        verbose_name='Ответ почтового сервера',
    )
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Рассылка',
    )
    recipient = models.ForeignKey(
        Recipient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mailing_attempts',
        verbose_name='Получатель',
    )

    class Meta:
        verbose_name = 'Попытка рассылки'
        verbose_name_plural = 'Попытки рассылок'
        ordering = ('-attempt_time',)

    def __str__(self):
        return (
            f'{self.mailing} — {self.get_status_display()} '
            f'({self.attempt_time:%d.%m.%Y %H:%M})'
        )

