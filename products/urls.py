from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.products, name='products'),  # All products
    path('products/<slug:category_slug>/', views.category_products, name='category_products'),  # Category wise products

    # Product-related
    #path('products/', views.products_list, name='products_list'),
    #path('products/<int:pk>/', views.product_detail, name='product_detail'),

    # Cart-related
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_item_id>/<str:action>/', views.update_cart_item, name='update_cart_item'),

    # Order-related
    path('orders/', views.orders, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    # Rental-related
    path('rental-products/', views.rental_products, name='rental_products'),
    path('rental-products/<int:pk>/', views.rental_product_detail, name='rental_product_detail'),
    path('rental-checkout/<int:pk>/', views.rental_checkout, name='rental_checkout'),
    path('rental-confirm/<int:pk>/', views.rental_confirm, name='rental_confirm'),
    path('rental-orders/', views.rental_orders, name='rental_orders'),
    path('cancel-rental-order/<int:order_id>/', views.cancel_rental_order, name='cancel_rental_order'),
    # Flash Sale URLs
    path('flash-sale/', views.flash_sale, name='flash_sale'),
    path('flash-sale/purchase/<int:pk>/', views.purchase_flash_sale, name='purchase_flash_sale'),
    path("flash-sale/<int:pk>/", views.flash_sale_detail, name="flash_sale_detail"),
    path("checkout/<int:pk>/", views.checkout, name="checkout"),
    path('flash-sale/<int:pk>/checkout/', views.flash_sale_checkout, name='flash_sale_checkout'),
    path('product/flash-sale/<int:pk>/', views.flash_sale_detail, name='flash_sale_detail'),
    path('flash-sale/', views.flash_sale_list, name='flash_sale'),
    # Pre-order URLs
    path('preorder-products/', views.preorder_products, name='preorder_products'),
    path('preorder-products/<int:pk>/', views.preorder_product_detail, name='preorder_product_detail'),
    path('add-to-preorder-cart/<int:product_id>/', views.add_to_preorder_cart, name='add_to_preorder_cart'),
    path('preorder-cart/', views.preorder_cart, name='preorder_cart'),
    path('preorder-cart/update/<int:preorder_item_id>/<str:action>/', views.update_preorder_cart_item, name='update_preorder_cart_item'),
    path('preorder-checkout/', views.preorder_checkout, name='preorder_checkout'),
    path('confirm-preorder/', views.confirm_preorder, name='confirm_preorder'),
    path('preorder-orders/', views.preorder_orders, name='preorder_orders'),
    path('preorder-orders/<int:preorder_id>/', views.preorder_order_detail, name='preorder_order_detail'),
    path('preorder/<int:preorder_id>/cancel/', views.cancel_preorder, name='cancel_preorder'),
]
