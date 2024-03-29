
class OrdersMixin:

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.get_orders()


class PaymentLinksMixin:

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.get_orders().get_pl()
