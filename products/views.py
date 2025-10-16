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
from payments.models import Order as PaymentOrder
from django.utils import timezone
import datetime
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

def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'product_detail.html', {'product': product})

def checkout(request, id):
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method')
        
        if not address or not phone or not payment_method:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'checkout.html', {'product': product})
        
        # Store checkout data in session
        request.session['single_product_checkout'] = {
            'product_id': product.id,
            'product_name': product.name,
            'product_price': float(product.price),
            'address': address,
            'phone': phone,
            'payment_method': payment_method,
        }
        
        # Create a payment order and redirect to SSLCOMMERZ
        description = f"{product.name} x1"
        order = PaymentOrder.objects.create(
            user=request.user,
            amount=float(product.price),
            description=description
        )
        return redirect('payments:sslcz_start', order_id=order.id)
    
    return render(request, 'checkout.html', {'product': product})

def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})

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
    return render(request, 'Login.html')


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
    cart_item, created = CartItem.objects.get_or_create(
        user=user, 
        product=product, 
        product_type='regular',
        defaults={'quantity': 1}
    )

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
def cart_checkout(request):
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
            return redirect('cart_checkout')

        request.session['checkout_address'] = address
        request.session['checkout_phone'] = phone
        request.session['checkout_payment_method'] = payment_method
        request.session['checkout_total_price'] = total_price

        # If not Cash on Delivery, create an order and redirect to SSLCOMMERZ
        if payment_method.lower() != 'cash on delivery':
            description = ', '.join([f"{item.product.name} x{item.quantity}" for item in cart_items])[:250]
            order = PaymentOrder.objects.create(
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


@login_required
def confirm_order(request):
    user = request.user
    
    # Check if this is a single product order or cart order
    single_product_data = request.session.get('single_product_checkout')
    
    if single_product_data:
        # Handle single product order
        address = single_product_data.get('address')
        phone = single_product_data.get('phone')
        total_price = single_product_data.get('product_price')
        payment_method = single_product_data.get('payment_method')
        product_id = single_product_data.get('product_id')
        product_name = single_product_data.get('product_name')
        
        if not address or not phone or not total_price or not payment_method or not product_id:
            messages.error(request, "Checkout details are missing. Please restart the process.")
            return redirect('product_checkout', id=product_id)
        
        # Get the product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            messages.error(request, "Product not found.")
            return redirect('home')
            
        context = {
            'single_product': True,
            'product': product,
            'address': address,
            'phone': phone,
            'total_price': total_price,
            'payment_method': payment_method,
        }
        
    else:
        # Handle cart-based order
        cart_items = CartItem.objects.filter(user=user).select_related('product')
        address = request.session.get('checkout_address')
        phone = request.session.get('checkout_phone')
        total_price = request.session.get('checkout_total_price')
        payment_method = request.session.get('checkout_payment_method')

        if not address or not phone or not total_price or not payment_method:
            messages.error(request, "Checkout details are missing. Please restart the process.")
            return redirect('cart_checkout')
            
        context = {
            'single_product': False,
            'cart_items': cart_items,
            'address': address,
            'phone': phone,
            'total_price': total_price,
            'payment_method': payment_method,
        }

    if request.method == 'POST':
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    total_price=total_price,
                    address=address,
                    phone=phone,
                    payment_method=payment_method
                )

                if single_product_data:
                    # Handle single product order
                    product = Product.objects.get(id=product_id)
                    
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=1,
                        price=total_price,
                    )
                    
                    # Update product stock
                    product.stock -= 1
                    if product.stock <= 0:
                        product.is_available = False
                    product.save()
                    
                    # Clear single product session data
                    request.session.pop('single_product_checkout', None)
                    
                else:
                    # Handle cart-based order
                    for item in cart_items:
                        if not item.product:
                            raise Exception("Product not found in cart item.")

                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            quantity=item.quantity,
                            price=item.get_total_price(),
                        )
                        item.product.stock -= item.quantity
                        if item.product.stock <= 0:
                            item.product.is_available = False
                        item.product.save()

                    cart_items.delete()

                    # Clear cart session data
                    for key in ['checkout_address', 'checkout_phone', 'checkout_payment_method', 'checkout_total_price']:
                        request.session.pop(key, None)

                messages.success(request, f"Order placed successfully! Order ID: {order.id}")
                print(f"Order ID: {order.id}")
                return redirect('thanks')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            print(f"Error: {str(e)}")
            if single_product_data:
                return redirect('product_checkout', id=product_id)
            else:
                return redirect('cart_checkout')

    return render(request, 'confirm_order.html', context)


def thanks(request):
    return render(request, 'thanks.html')


@login_required(login_url='login')
def orders(request):
    user = request.user
    orders = Order.objects.filter(user=user).prefetch_related('items__product')
    flash_sale_orders = FlashSaleOrder.objects.filter(user=user)

    return render(request, 'orders.html', {
        'orders': orders,
        'flash_sale_orders': flash_sale_orders
    })


@login_required(login_url='login')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_details.html', {'order': order})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status == 'Pending':
        # Restore the stock of the products in the order
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()

        # Delete the order
        order.delete()
        messages.success(request, 'Order canceled successfully.')
    else:
        messages.error(request, 'Only pending orders can be canceled.')

    return redirect('orders')





def rental_products(request):
    products = ProductRent.objects.filter(available=True)
    return render(request, 'rental_products.html', {'products': products})

# Rental product detail
def rental_product_detail(request, pk):
    product = get_object_or_404(ProductRent, id=pk)
    return render(request, 'rental_product_detail.html', {'product': product})

# Rental checkout: choose start & end dates
@login_required
def rental_checkout(request, pk):
    product = get_object_or_404(ProductRent, id=pk)

    if request.method == 'POST':
        rental_start_date = request.POST.get('rental_start_date')
        rental_end_date = request.POST.get('rental_end_date')

        if not rental_start_date or not rental_end_date:
            messages.error(request, "Please select rental start and end dates.")
            return redirect('rental_product_detail', pk=product.id)

        try:
            rental_start_date = datetime.datetime.strptime(rental_start_date, '%Y-%m-%d').date()
            rental_end_date = datetime.datetime.strptime(rental_end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('rental_product_detail', pk=product.id)

        if rental_end_date <= rental_start_date:
            messages.error(request, "Rental end date must be after the start date.")
            return redirect('rental_product_detail', pk=product.id)

        request.session['rental_start_date'] = rental_start_date.strftime('%Y-%m-%d')
        request.session['rental_end_date'] = rental_end_date.strftime('%Y-%m-%d')

        return redirect('rental_confirm', pk=product.id)

    return render(request, 'rental_checkout.html', {'product': product})

# Confirm rental order

# Confirm rental order
@login_required
def rental_confirm(request, pk):
    product = get_object_or_404(ProductRent, id=pk)
    rental_start_date = request.session.get('rental_start_date')
    rental_end_date = request.session.get('rental_end_date')

    if not rental_start_date or not rental_end_date:
        messages.error(request, "Rental dates missing. Please restart the process.")
        return redirect('rental_product_detail', pk=product.id)

    rental_start_date = datetime.datetime.strptime(rental_start_date, '%Y-%m-%d').date()
    rental_end_date = datetime.datetime.strptime(rental_end_date, '%Y-%m-%d').date()

    if request.method == 'POST':
        try:
            with transaction.atomic():
                rental_days = (rental_end_date - rental_start_date).days
                total_price = rental_days * product.rent_price_per_day
                
                # Store rental details in session for payment
                request.session['rental_product_id'] = product.id
                request.session['rental_start_date'] = rental_start_date.strftime('%Y-%m-%d')
                request.session['rental_end_date'] = rental_end_date.strftime('%Y-%m-%d')
                request.session['rental_total_price'] = float(total_price)
                request.session['rental_payment_method'] = 'SSLCommerz'
                
                # Create payment order and redirect to SSLCommerz
                description = f"Rental: {product.title} from {rental_start_date} to {rental_end_date}"
                payment_order = PaymentOrder.objects.create(
                    user=request.user,
                    amount=total_price,
                    description=description
                )
                return redirect('payments:sslcz_start', order_id=payment_order.id)
                    
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('rental_product_detail', pk=product.id)

    rental_days = (rental_end_date - rental_start_date).days
    total_price = rental_days * product.rent_price_per_day

    return render(request, 'rental_confirm.html', {
        'product': product,
        'rental_start_date': rental_start_date,
        'rental_end_date': rental_end_date,
        'total_price': total_price,
    })

# List rental orders
@login_required
def rental_orders(request):
    orders = RentalOrder.objects.filter(user=request.user).order_by('-id')
    return render(request, 'rental_orders.html', {"orders": orders})

# Cancel rental order
@login_required
def cancel_rental_order(request, order_id):
    order = get_object_or_404(RentalOrder, id=order_id, user=request.user)
    if order.status in ["Pending", "Confirmed"]:
        order.status = "Cancelled"
        order.save()
        messages.success(request, "Rental order cancelled successfully.")
    else:
        messages.error(request, "This order cannot be cancelled.")
    return redirect('rental_orders')

def flash_sale(request):
    now = timezone.now()
    flash_sale_products = FlashSaleProduct.objects.filter(start_time__lte=now, end_time__gte=now)
    return render(request, 'flash_sale.html', {'flash_sale_products': flash_sale_products})

def purchase_flash_sale(request, pk):
    # Dummy purchase logic (implement your own)
    # You can create an Order model and save purchase info here
    return redirect('flash_sale')

def flash_sale_detail(request, pk):
    product = get_object_or_404(FlashSaleProduct, pk=pk)
    return render(request, "flash_sale_detail.html", {"product": product})

def flash_sale_checkout(request, pk):
    product = get_object_or_404(FlashSaleProduct, pk=pk)

    if request.method == "POST":
        address = request.POST.get("address")
        phone = request.POST.get("phone")

        # Save order (assuming you have a model FlashSaleOrder)
        order = FlashSaleOrder.objects.create(
            user=request.user,
            product=product,
            quantity=1,  # default 1 for Buy Now
            address=address,
            phone=phone,
            total_price=product.get_sale_price(),
        )

        return redirect("order_success")  # redirect to a success page

    return render(request, "flash_sale_checkout.html", {
        "cart_items": [{"product": product, "quantity": 1, "get_total_price": product.get_sale_price()}],
        "total_price": product.get_sale_price(),
    })

def flash_sale(request):
    flash_sale_products = FlashSaleProduct.objects.all()
    return render(request, "flash_sale.html", {"flash_sale_products": flash_sale_products})


def flash_sale_list(request):
    products = FlashSaleProduct.objects.all()
    return render(request, 'flash_sale.html', {'products': products})

@login_required(login_url='login')
def flash_sale_checkout(request, pk):
    # Get the product
    product = get_object_or_404(FlashSaleProduct, pk=pk)
    
    # Calculate total price
    total_price = product.get_sale_price()
    
    if request.method == "POST":
        address = request.POST.get("address")
        phone = request.POST.get("phone")
        
        if not address or not phone:
            messages.error(request, "Please fill in all required fields.")
            return render(request, "flash_sale_checkout.html", {
                "product": product,
                "total_price": total_price
            })
        
        # Store flash sale order details in session for payment processing
        request.session['flash_sale_product_id'] = product.id
        request.session['flash_sale_address'] = address
        request.session['flash_sale_phone'] = phone
        request.session['flash_sale_total_price'] = float(total_price)
        request.session['flash_sale_quantity'] = 1
        
        # Create payment order and redirect to SSLCommerz
        description = f"Flash Sale: {product.name}"
        order = PaymentOrder.objects.create(
            user=request.user,
            amount=total_price,
            description=description
        )
        return redirect('payments:sslcz_start', order_id=order.id)
    
    return render(request, "flash_sale_checkout.html", {
        "product": product,
        "total_price": total_price
    })

# Pre-order views
def preorder_products(request):
    now = timezone.now()
    preorder_products = PreOrderProduct.objects.filter(
        is_active=True,
        preorder_start_date__lte=now,
        preorder_end_date__gte=now
    )
    return render(request, 'preorder.html', {'preorder_products': preorder_products})


def preorder_product_detail(request, pk):
    product = get_object_or_404(PreOrderProduct, pk=pk)
    return render(request, 'preorder_detail.html', {'product': product})


@login_required(login_url='login')
def add_to_preorder_cart(request, product_id):
    product = get_object_or_404(PreOrderProduct, id=product_id)
    user = request.user

    if not product.is_preorder_available():
        messages.error(request, "This pre-order is no longer available.")
        return redirect('preorder_products')

    # Check if the product is already in the preorder cart
    preorder_item, created = PreOrderItem.objects.get_or_create(user=user, preorder_product=product)

    if not created:
        # If the item already exists, increase the quantity
        if product.preorder_slots_remaining() > preorder_item.quantity:
            preorder_item.quantity += 1
            preorder_item.save()
            messages.success(request, f"{product.name} quantity increased in pre-order cart.")
        else:
            messages.warning(request, "No more pre-order slots available.")
    else:
        messages.success(request, f"{product.name} added to pre-order cart.")

    return redirect('preorder_cart')


@login_required(login_url='login')
def preorder_cart(request):
    user = request.user
    preorder_items = PreOrderItem.objects.filter(user=user)

    # Calculate the total price of items in the preorder cart
    total_price = preorder_items.aggregate(
        total_price=Sum(F('quantity') * F('preorder_product__price'))
    )['total_price'] or 0

    return render(request, 'preorder_cart.html', {
        'preorder_items': preorder_items,
        'total_price': total_price,
    })


@login_required(login_url='login')
def update_preorder_cart_item(request, preorder_item_id, action):
    preorder_item = get_object_or_404(PreOrderItem, id=preorder_item_id, user=request.user)
    
    if action == 'increase':
        if preorder_item.preorder_product.preorder_slots_remaining() > preorder_item.quantity:
            preorder_item.quantity += 1
            preorder_item.save()
            messages.success(request, f"Increased {preorder_item.preorder_product.name} quantity.")
        else:
            messages.warning(request, "No more pre-order slots available.")
    elif action == 'decrease':
        if preorder_item.quantity > 1:
            preorder_item.quantity -= 1
            preorder_item.save()
            messages.success(request, f"Decreased {preorder_item.preorder_product.name} quantity.")
        else:
            preorder_item.delete()
            messages.success(request, f"Removed {preorder_item.preorder_product.name} from pre-order cart.")
    elif action == 'remove':
        preorder_item.delete()
        messages.success(request, f"Removed {preorder_item.preorder_product.name} from pre-order cart.")
    else:
        messages.error(request, "Invalid action.")
    
    return redirect('preorder_cart')


@login_required
def preorder_checkout(request):
    user = request.user
    preorder_items = PreOrderItem.objects.filter(user=user).select_related('preorder_product')

    if not preorder_items.exists():
        messages.warning(request, "Your pre-order cart is empty.")
        return redirect('preorder_cart')

    total_price = float(sum(item.get_total_price() for item in preorder_items))

    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method')

        if not address or not phone or not payment_method:
            messages.error(request, "Please fill in all required fields.")
            return redirect('preorder_checkout')

        request.session['preorder_checkout_address'] = address
        request.session['preorder_checkout_phone'] = phone
        request.session['preorder_checkout_payment_method'] = payment_method
        request.session['preorder_checkout_total_price'] = total_price

        # Create payment order and redirect to SSLCOMMERZ
        description = ', '.join([f"{item.preorder_product.name} x{item.quantity}" for item in preorder_items])[:250]
        order = PaymentOrder.objects.create(
            user=request.user,
            amount=total_price,
            description=f"PreOrder: {description}"
        )
        return redirect('payments:sslcz_start', order_id=order.id)

    return render(request, 'preorder_checkout.html', {
        'preorder_items': preorder_items,
        'total_price': total_price,
    })


@login_required
def confirm_preorder(request):
    user = request.user
    preorder_items = PreOrderItem.objects.filter(user=user).select_related('preorder_product')

    address = request.session.get('preorder_checkout_address')
    phone = request.session.get('preorder_checkout_phone')
    total_price = request.session.get('preorder_checkout_total_price')
    payment_method = request.session.get('preorder_checkout_payment_method')

    if not address or not phone or not total_price or not payment_method:
        messages.error(request, "Pre-order checkout details are missing. Please restart the process.")
        return redirect('preorder_checkout')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                preorder = PreOrder.objects.create(
                    user=user,
                    total_price=total_price,
                    address=address,
                    phone=phone,
                    payment_method=payment_method
                )

                for item in preorder_items:
                    if not item.preorder_product:
                        raise Exception("Pre-order product not found in cart item.")

                    PreOrderOrderItem.objects.create(
                        preorder=preorder,
                        preorder_product=item.preorder_product,
                        quantity=item.quantity,
                        price=item.get_total_price(),
                    )
                    
                    # Update preorder count
                    item.preorder_product.current_preorders += item.quantity
                    item.preorder_product.save()

                preorder_items.delete()

                # Clear session
                for key in ['preorder_checkout_address', 'preorder_checkout_phone', 'preorder_checkout_payment_method', 'preorder_checkout_total_price']:
                    request.session.pop(key, None)

                messages.success(request, f"Pre-order placed successfully! Pre-order ID: {preorder.id}")
                return redirect('preorder_orders')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('preorder_checkout')

    return render(request, 'preorder_confirm.html', {
        'preorder_items': preorder_items,
        'total_price': total_price,
        'address': address,
        'phone': phone,
        'payment_method': payment_method,
    })


@login_required(login_url='login')
def preorder_orders(request):
    user = request.user
    preorders = PreOrder.objects.filter(user=user).prefetch_related('items__preorder_product')
    return render(request, 'preorder_orders.html', {'preorders': preorders})


@login_required(login_url='login')
def preorder_order_detail(request, preorder_id):
    preorder = get_object_or_404(PreOrder, id=preorder_id, user=request.user)
    return render(request, 'preorder_order_details.html', {'preorder': preorder})


@login_required
def cancel_preorder(request, preorder_id):
    preorder = get_object_or_404(PreOrder, id=preorder_id, user=request.user)

    if preorder.status == 'Pending':
        # Restore the preorder slots
        for item in preorder.items.all():
            item.preorder_product.current_preorders -= item.quantity
            item.preorder_product.save()

        # Cancel the preorder
        preorder.status = 'Cancelled'
        preorder.save()
        messages.success(request, 'Pre-order cancelled successfully.')
    else:
        messages.error(request, 'Only pending pre-orders can be cancelled.')

    return redirect('preorder_orders')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you can add logic to save the contact form data to database
        # or send an email notification
        
        # For now, we'll just show a success message
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('contact')
    
    return render(request, 'contact.html')