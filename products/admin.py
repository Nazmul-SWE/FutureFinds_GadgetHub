from django.contrib import admin

from .models import (Product, Category, CartItem, ProductRent, RentalOrderItem, RentalOrder, 
                     Order, OrderItem, FlashSaleProduct, PreOrderProduct, PreOrder, 
                     PreOrderItem, PreOrderOrderItem, FlashSaleOrder)

# Register your models here.
admin.site.register(Product)
admin.site.register(Category)
admin.site.register(CartItem)
admin.site.register(ProductRent)
admin.site.register(RentalOrderItem)
admin.site.register(RentalOrder)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(FlashSaleProduct)

# Pre-order models
admin.site.register(PreOrderProduct)
admin.site.register(PreOrder)
admin.site.register(PreOrderItem)
admin.site.register(PreOrderOrderItem)
admin.site.register(FlashSaleOrder)


