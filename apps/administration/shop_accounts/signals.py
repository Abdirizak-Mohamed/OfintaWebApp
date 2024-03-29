

def shop_account_removed(sender, instance, using, *args, **kwargs):
    """
    Calling after shop account removed
    """
    from apps.core.models import UserRoles
    # if shop owner was removed - removed all its managers
    if instance.role == UserRoles.OWNER:
        shop = instance.shop
        shop_managers = shop.users.all()
        shop_managers.delete()
