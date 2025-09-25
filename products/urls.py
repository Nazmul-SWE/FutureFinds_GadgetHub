from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page shows categories
    path('products/', views.products, name='products'),  # All products
    path('products/<slug:category_slug>/', views.category_products, name='category_products'),  # Category wise products

    path('', views.home, name='home'),

    # Product-related
    #path('products/', views.products_list, name='products_list'),
    #path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # Rental-related
    path('rental-products/', views.rental_products, name='rental_products'),
    path('rental-products/<int:pk>/', views.rental_product_detail, name='rental_product_detail'),
    path('rental-checkout/<int:pk>/', views.rental_checkout, name='rental_checkout'),
    path('rental-confirm/<int:pk>/', views.rental_confirm, name='rental_confirm'),
    path('rental-orders/', views.rental_orders, name='rental_orders'),
    path('cancel-rental-order/<int:order_id>/', views.cancel_rental_order, name='cancel_rental_order'),
    path('flash-sale/', views.flash_sale, name='flash_sale'),
    path('flash-sale/purchase/<int:pk>/', views.purchase_flash_sale, name='purchase_flash_sale'),
    path("flash-sale/<int:pk>/", views.flash_sale_detail, name="flash_sale_detail"),
    path("checkout/<int:pk>/", views.checkout, name="checkout"),
    path('flash-sale/<int:pk>/checkout/', views.flash_sale_checkout, name='flash_sale_checkout'),
]
