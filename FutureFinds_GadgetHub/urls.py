"""
URL configuration for FutureFinds project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include

from products.views import SignUp, login, logout
from products.views import *
urlpatterns = [

    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('product/', include('products.urls')),
    path('products/', products),

    path('signup/', SignUp, name='signup'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),



# Shop URLs
    path('products/',products, name='products'),
    #path('shop/<int:product_id>/', product_detail, name='product_detail'),
    path('cart/', cart, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:cart_item_id>/<str:action>/', update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:cart_item_id>/', update_cart_item, name='remove_cart_item'),
    path('checkout/', checkout, name='checkout'),
    path('confirm-order/', confirm_order, name='confirm_order'),
    #path('thanks/', thanks, name='thanks'),
    path('orders/',orders, name='orders'),
    path('orders/<int:order_id>/',order_detail, name='order_detail'),
    path('order/<int:order_id>/cancel/', cancel_order, name='cancel_order'),


]
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import include, path
urlpatterns += [ path('payments/', include('payments.urls')), ]
