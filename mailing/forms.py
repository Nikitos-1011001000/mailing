from django import forms

from mailing.models import Mailing, Message, Recipient


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = ('email', 'full_name', 'comment')
        widgets = {
            'comment': forms.Textarea(
                attrs={'rows': 4}
            ),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('subject', 'body')
        widgets = {
            'body': forms.Textarea(
                attrs={'rows': 8}
            ),
        }


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = (
            'start_time',
            'end_time',
            'message',
            'recipients',
        )
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
            ),
            'recipients': forms.SelectMultiple(
                attrs={'size': 8},
            ),
        }