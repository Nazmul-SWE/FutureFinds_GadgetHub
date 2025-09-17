from django.urls import path
from . import views

app_name = 'payments'
urlpatterns = [
    path('create/', views.create_test_order, name='create_order'),
    path('sslcz/start/<int:order_id>/', views.start_sslcz_payment, name='sslcz_start'),
    path('sslcz/success/', views.sslcz_success, name='sslcz_success'),
    path('sslcz/fail/', views.sslcz_fail, name='sslcz_fail'),
    path('sslcz/cancel/', views.sslcz_cancel, name='sslcz_cancel'),
    path('sslcz/ipn/', views.sslcz_ipn, name='sslcz_ipn'),
    path('list/', views.payment_list, name='list'),
]
