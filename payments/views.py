from django.shortcuts import redirect, render, get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.contrib.auth.models import User
from .models import Order, Transaction
import uuid
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError
from products.models import CartItem


def create_test_order(request):
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        amount=50.00,
        description='Test order from project'
    )
    return render(request, 'payments/create_order.html', {'order': order})


def start_sslcz_payment(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    tran_id = f"ORDER{order.id}-{uuid.uuid4().hex[:8]}"
    tx = Transaction.objects.create(order=order, gateway='sslcommerz', amount=order.amount, transaction_id=tran_id)

    store_id = getattr(settings, 'SSLCOMMERZ_STORE_ID', '')
    store_passwd = getattr(settings, 'SSLCOMMERZ_STORE_PASS', '')
    sandbox = getattr(settings, 'SSLCOMMERZ_SANDBOX', True)
    init_url_v4 = 'https://sandbox.sslcommerz.com/gwprocess/v4/api.php' if sandbox else 'https://securepay.sslcommerz.com/gwprocess/v4/api.php'
    init_url_v3 = 'https://sandbox.sslcommerz.com/gwprocess/v3/api.php' if sandbox else 'https://securepay.sslcommerz.com/gwprocess/v3/api.php'

    success_url = request.build_absolute_uri('/payments/sslcz/success/')
    fail_url = request.build_absolute_uri('/payments/sslcz/fail/')
    cancel_url = request.build_absolute_uri('/payments/sslcz/cancel/')
    ipn_url = request.build_absolute_uri('/payments/sslcz/ipn/')

    # Minimal required payload; extend as needed
    # Pull address/phone from checkout session if present
    sess_addr = request.session.get('checkout_address') or 'Address'
    sess_phone = request.session.get('checkout_phone') or '00000000000'

    # Ensure valid email for gateway; fallback if blank/invalid
    user_email = ''
    if request.user.is_authenticated:
        user_email = (request.user.email or '').strip()
    if not user_email or '@' not in user_email:
        user_email = 'customer@example.com'

    payload = {
        'store_id': store_id,
        'store_passwd': store_passwd,
        'total_amount': format(order.amount, '.2f'),
        'currency': order.currency,
        'tran_id': tran_id,
        'success_url': success_url,
        'fail_url': fail_url,
        'cancel_url': cancel_url,
        'ipn_url': ipn_url,
        'emi_option': 0,
        'cus_name': request.user.get_username() or 'Guest',
        'cus_email': user_email,
        'cus_add1': sess_addr,
        'cus_city': 'City',
        'cus_postcode': '0000',
        'cus_country': 'Bangladesh',
        'cus_phone': sess_phone,
        'shipping_method': 'NO',
        'product_name': order.description or 'Order Items',
        'product_category': 'General',
        'product_profile': 'general'
    }

    def call_init(url):
        data = urlencode(payload).encode('utf-8')
        req = Request(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        with urlopen(req, timeout=20) as resp:
            resp_body = resp.read().decode('utf-8')
            try:
                return json.loads(resp_body)
            except json.JSONDecodeError:
                return {'raw': resp_body}

    try:
        resp_json = call_init(init_url_v4)
    except URLError as e:
        resp_json = {'error': str(e)}

    gateway_url = resp_json.get('GatewayPageURL') or resp_json.get('redirectGatewayURL')
    # Fallback to v3 if v4 did not return a URL
    if not gateway_url:
        try:
            resp_json_v3 = call_init(init_url_v3)
            gateway_url = resp_json_v3.get('GatewayPageURL') or resp_json_v3.get('redirectGatewayURL')
            if gateway_url:
                resp_json = resp_json_v3
        except URLError:
            pass

    if not gateway_url:
        # record response for debugging
        tx.raw_response = resp_json
        tx.success = False
        tx.save()
        return render(request, 'payments/error.html', {
            'msg': 'Gateway URL not received from SSLCOMMERZ.',
            'resp': resp_json
        })

    return redirect(gateway_url)


@csrf_exempt
def sslcz_success(request):
    # SSLCOMMERZ sends POST data including val_id to success_url
    val_id = request.POST.get('val_id')
    tran_id = request.POST.get('tran_id') or request.GET.get('tran_id')
    if not tran_id:
        return render(request, 'payments/error.html', {'msg': 'Missing tran_id'})

    tx = Transaction.objects.filter(transaction_id=tran_id).order_by('-created_at').first()
    if not tx:
        return render(request, 'payments/error.html', {'msg': 'Transaction not found'})

    # Validate with SSLCOMMERZ
    store_id = getattr(settings, 'SSLCOMMERZ_STORE_ID', '')
    store_passwd = getattr(settings, 'SSLCOMMERZ_STORE_PASS', '')
    sandbox = getattr(settings, 'SSLCOMMERZ_SANDBOX', True)
    base_url = 'https://sandbox.sslcommerz.com' if sandbox else 'https://securepay.sslcommerz.com'
    if not val_id:
        return render(request, 'payments/error.html', {'msg': 'Missing val_id'})

    query = urlencode({
        'val_id': val_id,
        'store_id': store_id,
        'store_passwd': store_passwd,
        'v': 1,
        'format': 'json'
    })
    verify_url = f"{base_url}/validator/api/validationserverAPI.php?{query}"

    try:
        with urlopen(verify_url, timeout=15) as resp:
            resp_body = resp.read().decode('utf-8')
            resp_json = json.loads(resp_body)
    except (URLError, json.JSONDecodeError):
        return render(request, 'payments/error.html', {'msg': 'Failed to validate payment.'})

    status = resp_json.get('status')
    if status != 'VALID' and status != 'VALIDATED':
        tx.raw_response = resp_json
        tx.success = False
        tx.save()
        order = tx.order
        order.status = 'failed'
        order.save()
        return render(request, 'payments/error.html', {'msg': 'Payment not valid.'})

    tx.raw_response = resp_json
    tx.success = True
    tx.save()
    order = tx.order
    order.status = 'paid'
    order.save()

    # Handle successful payment - check if it's a regular order or rental order
    if order.user_id:
        import datetime
        
        # Check if this is a rental order (has rental data in session)
        rental_product_id = request.session.get('rental_product_id')
        
        if rental_product_id:
            # This is a rental order
            from products.models import ProductRent, RentalOrder
            
            try:
                rental_start_date = request.session.get('rental_start_date')
                rental_end_date = request.session.get('rental_end_date')
                
                if rental_start_date and rental_end_date:
                    rental_start_date = datetime.datetime.strptime(rental_start_date, '%Y-%m-%d').date()
                    rental_end_date = datetime.datetime.strptime(rental_end_date, '%Y-%m-%d').date()
                    
                    product = ProductRent.objects.get(id=rental_product_id)
                    
                    # Create rental order
                    rental_order = RentalOrder.objects.create(
                        user_id=order.user_id,
                        product=product,
                        rental_start_date=rental_start_date,
                        rental_end_date=rental_end_date,
                        status='Confirmed'
                    )
                    
                    # Clear rental session data
                    for key in ['rental_product_id', 'rental_start_date', 'rental_end_date', 'rental_total_price', 'rental_payment_method']:
                        request.session.pop(key, None)
                        
            except Exception as e:
                print(f"Error creating rental order: {str(e)}")
        else:
            # This is a regular product order
            from products.models import Order as ProductOrder, OrderItem
            
            # Get cart items before clearing
            cart_items = CartItem.objects.filter(user_id=order.user_id)
            
            # Get address and phone from session or payment response
            user_obj = User.objects.get(id=order.user_id)
            address = request.session.get('checkout_address', '')
            phone = request.session.get('checkout_phone', '')
            
            # Create order in products app
            product_order = ProductOrder.objects.create(
                user=user_obj,
                total_price=order.amount,
                address=address,
                phone=phone,
                payment_method='SSLCommerz',
                status='Confirmed'
            )
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=product_order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.get_total_price(),
                )
                # Update stock
                item.product.stock -= item.quantity
                if item.product.stock <= 0:
                    item.product.is_available = False
                item.product.save()
            
            # Clear cart
            cart_items.delete()
            
            # Clear session data
            for key in ['checkout_address', 'checkout_phone', 'checkout_payment_method', 'checkout_total_price']:
                request.session.pop(key, None)
    
    # Check if this was a rental order to redirect appropriately
    is_rental = 'rental_product_id' in request.session
    
    return render(request, 'payments/success.html', {
        'order': order, 
        'tx': tx,
        'is_rental': is_rental
    })


@csrf_exempt
def sslcz_fail(request):
    tran_id = request.POST.get('tran_id') or request.GET.get('tran_id')
    tx = Transaction.objects.filter(transaction_id=tran_id).order_by('-created_at').first() if tran_id else None
    if tx:
        tx.raw_response = {'status': 'FAILED'}
        tx.success = False
        tx.save()
        order = tx.order
        order.status = 'failed'
        order.save()
    return render(request, 'payments/error.html', {'msg': 'Payment failed.'})


@csrf_exempt
def sslcz_cancel(request):
    tran_id = request.POST.get('tran_id') or request.GET.get('tran_id')
    tx = Transaction.objects.filter(transaction_id=tran_id).order_by('-created_at').first() if tran_id else None
    if tx:
        tx.raw_response = {'status': 'CANCELLED'}
        tx.success = False
        tx.save()
        order = tx.order
        order.status = 'cancelled'
        order.save()
    return render(request, 'payments/error.html', {'msg': 'Payment cancelled.'})


@csrf_exempt
def sslcz_ipn(request):
    # Optional IPN handler
    data = request.POST.dict()
    tran_id = data.get('tran_id')
    if not tran_id:
        return HttpResponseBadRequest('Missing tran_id')
    tx = Transaction.objects.filter(transaction_id=tran_id).order_by('-created_at').first()
    if not tx:
        return HttpResponseBadRequest('Transaction not found')
    tx.raw_response = data
    tx.save()
    return render(request, 'payments/success.html', {'order': tx.order, 'tx': tx})


def payment_list(request):
    orders = Order.objects.order_by('-created_at')[:20]
    return render(request, 'payments/list.html', {'orders': orders})