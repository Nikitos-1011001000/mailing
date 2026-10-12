from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone

from mailing.models import Mailing, MailingAttempt


def send_mailing(mailing):
    """
    Запускает рассылку, отправляет письмо каждому получателю
    и создаёт попытки отправки одним batch-вызовом.
    """
    mailing.update_status()
    now = timezone.now()

    if not mailing.start_time <= now <= mailing.end_time:
        raise ValueError(
            'Рассылку нельзя запустить: текущее время '
            'не входит в разрешённый интервал отправки.'
        )

    attempts_to_create = []
    results = {
        'success': 0,
        'failed': 0,
    }

    for recipient in mailing.recipients.all():
        try:
            sent_count = send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )

            if sent_count:
                status = MailingAttempt.STATUS_SUCCESS
                server_response = 'Письмо принято к отправке.'
                results['success'] += 1
            else:
                status = MailingAttempt.STATUS_FAILED
                server_response = (
                    'Почтовый backend не подтвердил отправку.'
                )
                results['failed'] += 1

        except Exception as error:
            status = MailingAttempt.STATUS_FAILED
            server_response = str(error)
            results['failed'] += 1

        attempts_to_create.append(
            MailingAttempt(
                mailing=mailing,
                recipient=recipient,
                status=status,
                server_response=server_response,
            )
        )

    if attempts_to_create:
        MailingAttempt.objects.bulk_create(attempts_to_create)

    mailing.sent_count += results['success']
    mailing.failed_count += results['failed']

    mailing.save(
        update_fields=[
            'sent_count',
            'failed_count',
        ]
    )

    return results


def get_user_stats(user):
    """
    Возвращает общую статистику по рассылкам пользователя.
    """
    stats = Mailing.objects.filter(user=user).aggregate(
        total_sent=Sum('sent_count'),
        total_failed=Sum('failed_count'),
    )

    return {
        'total_sent': stats['total_sent'] or 0,
        'total_failed': stats['total_failed'] or 0,
    }