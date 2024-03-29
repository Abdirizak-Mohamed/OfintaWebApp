# django
from django.urls import path

# ofinta
from apps.management.chat.views import Chat


urlpatterns = [
    path('', Chat.as_view(), name='chat'),
]
