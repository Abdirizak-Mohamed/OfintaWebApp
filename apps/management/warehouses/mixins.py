
class WarehousesMixin:

    def get_queryset(self):
        user = self.request.user
        shop = user.shop
        return shop.warehouses.all()
