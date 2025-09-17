from django.shortcuts import render
from products.models import Product, Category


def home (request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'home.html', {'products': products, 'categories': categories})

def products (request):
    products = Product.objects.all()
    return render(request,'products.html',context={'products':products})

