from django.contrib import admin
from .models import Order, Transaction

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user','amount','currency','status','created_at')
    list_filter = ('status','currency')
    search_fields = ('id','user__username')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id','order','gateway','transaction_id','amount','success','created_at')
    list_filter = ('gateway','success')
    search_fields = ('transaction_id','order__id')
