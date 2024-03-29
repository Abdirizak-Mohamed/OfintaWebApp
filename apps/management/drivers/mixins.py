
class DriversMixin:

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.get_drivers()
