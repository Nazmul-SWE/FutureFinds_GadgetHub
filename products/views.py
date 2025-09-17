from django.shortcuts import render, get_object_or_404
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as django_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, F
from django.shortcuts import redirect
from django.http import HttpResponse
from payments.models import Order



def home(request):
    categories = Category.objects.all()
    return render(request, 'home.html', {'categories': categories})

def products(request):
    products = Product.objects.all()
    return render(request, 'products.html', {'products': products})

def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category)
    return render(request, 'products.html', {'products': products})

def SignUp(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken. Please choose a different username.')
            return render(request, 'signup.html')

        user = User.objects.create_user(username=username, email=email, password=password)

        request.session['signup_username'] = username
        request.session['signup_email'] = email
        request.session['signup_password'] = password

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'You have successfully signed up!')
            return redirect('login')
        else:
            messages.error(request, 'An error occurred while signing up. Please try again.')
            return render(request, 'Signup.html')

    return render(request, 'Signup.html')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the login credentials belong to a regular user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'You have successfully logged in!')
            return redirect('home')  # Redirect to the booking page

        else:
            # Authentication failed, display an error message
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    return render(request, 'login.html')


@login_required
def logout(request):
    django_logout(request)
    return redirect('home')

def products(request):
    # Get the category filter from the query parameters
    category_filter = request.GET.get('category', None)

    # Filter products based on category if provided, otherwise fetch all products
    if category_filter:
        products = Product.objects.filter(category__slug=category_filter, is_available=True)
    else:
        products = Product.objects.filter(is_available=True)

    # Fetch all unique categories for the filter dropdown
    categories = Category.objects.all()

    return render(request, 'products.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_filter,
    })

@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    # Check if the product is already in the cart
    cart_item, created = CartItem.objects.get_or_create(user=user, product=product)

    if not created:
        # If the item already exists, increase the quantity
        if product.stock > cart_item.quantity:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"{product.name} quantity increased.")
        else:
            messages.warning(request, "Insufficient stock available.")
    else:
        messages.success(request, f"{product.name} added to cart.")

    return redirect('cart')

@login_required(login_url='login')
def cart(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)

    # Calculate the total price of items in the cart
    total_price = cart_items.aggregate(
        total_price=Sum(F('quantity') * F('product__price'))
    )['total_price'] or 0

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })

@login_required(login_url='login')
def update_cart_item(request, cart_item_id, action):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)
    if action == 'increase':
        if cart_item.product.stock > cart_item.quantity:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Increased {cart_item.product.name} quantity.")
        else:
            messages.warning(request, "Insufficient stock available.")
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, f"Decreased {cart_item.product.name} quantity.")
        else:
            cart_item.delete()
            messages.success(request, f"Removed {cart_item.product.name} from cart.")
    elif action == 'remove':
        cart_item.delete()
        messages.success(request, f"Removed {cart_item.product.name} from cart.")
    else:
        messages.error(request, "Invalid action.")
    return redirect('cart')
@login_required
def checkout(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('product')

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    total_price = float(sum(item.get_total_price() for item in cart_items))

    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method')

        if not address or not phone or not payment_method:
            messages.error(request, "Please fill in all required fields.")
            return redirect('checkout')

        request.session['checkout_address'] = address
        request.session['checkout_phone'] = phone
        request.session['checkout_payment_method'] = payment_method
        request.session['checkout_total_price'] = total_price

        # If not Cash on Delivery, create an order and redirect to SSLCOMMERZ
        if payment_method.lower() != 'cash on delivery':
            description = ', '.join([f"{item.product.name} x{item.quantity}" for item in cart_items])[:250]
            order = Order.objects.create(
                user=request.user,
                amount=total_price,
                description=description
            )
            # Optionally clear cart only after payment success; so do not clear here
            return redirect('payments:sslcz_start', order_id=order.id)

        return redirect('confirm_order')

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })
