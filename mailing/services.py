from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from mailing.models import MailingAttempt


def send_mailing(mailing):
    """
    Вручную запускает рассылку и создаёт попытку
    для каждого получателя.
    """
    mailing.update_status()
    now = timezone.now()

    if not mailing.start_time <= now <= mailing.end_time:
        raise ValueError(
            'Рассылку нельзя запустить: текущее время '
            'не входит в разрешённый интервал отправки.'
        )

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
                MailingAttempt.objects.create(
                    mailing=mailing,
                    recipient=recipient,
                    status=MailingAttempt.STATUS_SUCCESS,
                    server_response='Письмо принято к отправке.',
                )
                results['success'] += 1
            else:
                MailingAttempt.objects.create(
                    mailing=mailing,
                    recipient=recipient,
                    status=MailingAttempt.STATUS_FAILED,
                    server_response=(
                        'Почтовый backend не подтвердил отправку.'
                    ),
                )
                results['failed'] += 1

        except Exception as error:
            MailingAttempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status=MailingAttempt.STATUS_FAILED,
                server_response=str(error),
            )
            results['failed'] += 1

    return results