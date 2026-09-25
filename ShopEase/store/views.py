import razorpay

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import Product, Order, OrderItem


def home(request):
    products = Product.objects.all()

    return render(request, 'store/home.html', {
        'products': products
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    return render(request, 'store/product_detail.html', {
        'product': product
    })


def add_to_cart(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get('cart', {})

    product_id = str(product_id)

    quantity = int(request.POST.get('quantity', 1))

    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


def cart(request):

    cart_data = request.session.get('cart', {})

    cart_items = []
    total = 0

    for product_id, quantity in cart_data.items():

        product = get_object_or_404(Product, id=product_id)

        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total,
    })


def remove_from_cart(request, product_id):

    cart = request.session.get('cart', {})

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


@login_required
def checkout(request):

    cart_data = request.session.get('cart', {})

    if not cart_data:
        return redirect('cart')

    cart_items = []
    total = 0

    for product_id, quantity in cart_data.items():

        product = get_object_or_404(Product, id=product_id)

        if quantity > product.stock:
            return render(request, 'store/checkout.html', {
                'error': f'Only {product.stock} units of {product.name} are available.',
                'cart_items': cart_items,
                'total': total,
            })

        subtotal = product.price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
        })

    if request.method == 'POST':

        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')

        if not all([
            full_name,
            email,
            phone,
            address,
            city,
            state,
            pincode
        ]):
            return render(request, 'store/checkout.html', {
                'error': 'Please fill in all the required fields.',
                'cart_items': cart_items,
                'total': total,
            })

        # Save checkout details temporarily in session.
        # Order will NOT be created here.
        request.session['checkout_data'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'address': address,
            'city': city,
            'state': state,
            'pincode': pincode,
        }

        request.session['checkout_cart'] = cart_data
        request.session.modified = True

        # Go to payment page
        return redirect('payment')

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total': total,
    })


@login_required
def payment(request):

    checkout_data = request.session.get('checkout_data')
    cart_data = request.session.get('checkout_cart')

    if not checkout_data or not cart_data:
        return redirect('checkout')

    total = 0

    for product_id, quantity in cart_data.items():

        product = get_object_or_404(Product, id=product_id)

        if quantity > product.stock:
            return redirect('checkout')

        total += product.price * quantity

    # Convert rupees into paise
    amount = int(total * 100)

    if amount <= 0:
        return redirect('cart')

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    payment_order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    # Save Razorpay order ID in session
    request.session['razorpay_order_id'] = payment_order["id"]
    request.session.modified = True

    context = {
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": amount,
        "display_amount": total,
        "order_id": payment_order["id"],
    }

    return render(request, "store/payment.html", context)


@login_required
def payment_success(request):

    checkout_data = request.session.get('checkout_data')
    cart_data = request.session.get('checkout_cart')
    razorpay_order_id = request.session.get('razorpay_order_id')

    if not checkout_data or not cart_data or not razorpay_order_id:
        return redirect('cart')

    payment_id = request.GET.get('razorpay_payment_id')
    received_order_id = request.GET.get('razorpay_order_id')
    signature = request.GET.get('razorpay_signature')

    # Check that all Razorpay response values are present
    if not payment_id or not received_order_id or not signature:
        return render(request, 'store/payment_success.html', {
            'error': 'Payment verification information is missing.'
        })

    # Make sure the Razorpay order belongs to this checkout
    if received_order_id != razorpay_order_id:
        return render(request, 'store/payment_success.html', {
            'error': 'Payment order verification failed.'
        })

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    # Verify Razorpay payment signature
    try:

        client.utility.verify_payment_signature({
            'razorpay_order_id': received_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })

    except Exception:

        return render(request, 'store/payment_success.html', {
            'error': 'Payment verification failed. Order was not placed.'
        })

    # Calculate total again
    total = 0

    for product_id, quantity in cart_data.items():

        product = get_object_or_404(Product, id=product_id)

        if quantity > product.stock:
            return render(request, 'store/payment_success.html', {
                'error': f'Only {product.stock} units of {product.name} are available. Order was not placed.'
            })

        total += product.price * quantity

    # NOW create the actual order
    order = Order.objects.create(
        user=request.user,
        full_name=checkout_data['full_name'],
        email=checkout_data['email'],
        phone=checkout_data['phone'],
        address=checkout_data['address'],
        city=checkout_data['city'],
        state=checkout_data['state'],
        pincode=checkout_data['pincode'],
        total_amount=total,
    )

    # Create order items and reduce stock
    for product_id, quantity in cart_data.items():

        product = get_object_or_404(
            Product,
            id=product_id
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price,
        )

        product.stock -= quantity
        product.save()

    # Clear cart and checkout information
    request.session['cart'] = {}
    request.session.pop('checkout_data', None)
    request.session.pop('checkout_cart', None)
    request.session.pop('razorpay_order_id', None)

    request.session.modified = True

    return redirect('order_success', order_id=order.id)


def order_success(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(request, 'store/order_success.html', {
        'order': order
    })


@login_required
def my_orders(request):

    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'store/my_orders.html', {
        'orders': orders
    })


@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(request, 'store/order_detail.html', {
        'order': order
    })


def register(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:

            return render(request, 'store/register.html', {
                'error': 'Passwords do not match.'
            })

        if User.objects.filter(username=username).exists():

            return render(request, 'store/register.html', {
                'error': 'Username already exists.'
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)

        return redirect('home')

    return render(request, 'store/register.html')


def user_login(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('home')

        return render(request, 'store/login.html', {
            'error': 'Invalid username or password.'
        })

    return render(request, 'store/login.html')


def user_logout(request):

    logout(request)

    return redirect('home')


@login_required
def account(request):

    orders_count = Order.objects.filter(
        user=request.user
    ).count()

    cart_data = request.session.get('cart', {})

    cart_count = sum(cart_data.values())

    return render(request, 'store/account.html', {
        'orders_count': orders_count,
        'cart_count': cart_count,
    })