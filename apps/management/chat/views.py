# django
from django.views.generic import CreateView

# ofinta
from apps.management.chat.forms import MessageForm
from apps.management.chat.models import Message


class Chat(CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'management/chat/chat.html'
