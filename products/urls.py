from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page shows categories
    path('products/', views.products, name='products'),  # All products
    path('products/<slug:category_slug>/', views.category_products, name='category_products'),  # Category wise products
]
