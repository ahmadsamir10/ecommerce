from django.contrib import admin
from .models import Item, OrderItem, Order, BillingAddress, Payment, ItemImage, PromoCode
# Register your models here.


admin.site.register(Item)
admin.site.register(ItemImage)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(BillingAddress)
admin.site.register(Payment)
admin.site.register(PromoCode)