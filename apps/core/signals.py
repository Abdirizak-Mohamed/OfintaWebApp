

def create_auth_token(sender, instance=None, created=False, **kwargs):
    from rest_framework.authtoken.models import Token
    if created:
        Token.objects.get_or_create(user=instance)
