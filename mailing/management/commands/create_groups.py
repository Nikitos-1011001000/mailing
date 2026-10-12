from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создаёт группу менеджеров и назначает права.'

    def handle(self, *args, **kwargs):
        group, created = Group.objects.get_or_create(
            name='Менеджеры',
        )

        permissions = Permission.objects.filter(
            codename__in=[
                'view_mailing',
                'view_message',
                'view_recipient',
                'view_mailingattempt',
                'view_user',
            ]
        )

        group.permissions.set(permissions)

        if created:
            self.stdout.write(
                self.style.SUCCESS('Группа «Менеджеры» создана.')
            )
        else:
            self.stdout.write('Группа «Менеджеры» уже существует.')