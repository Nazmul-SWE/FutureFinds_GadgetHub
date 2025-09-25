from django.contrib import admin

from .models import Product, Category, CartItem, ProductRent, RentalOrderItem, RentalOrder, Order, OrderItem,FlashSaleProduct

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
