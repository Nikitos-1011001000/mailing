from django.contrib import admin

from mailing.models import Mailing, MailingAttempt, Message, Recipient

admin.site.register(Recipient)
admin.site.register(Message)
admin.site.register(Mailing)
admin.site.register(MailingAttempt)