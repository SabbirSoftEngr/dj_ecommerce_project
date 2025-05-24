import requests
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth.models import User

from .models import Product, Order, OrderItem
from .forms import UserRegisterForm
from .utils import sslcommerz_create_session  # SSLCommerz helper function


class CustomLoginView(auth_views.LoginView):
    template_name = 'shop/login.html'


class CustomLogoutView(auth_views.LogoutView):
    template_name = 'shop/logout.html'


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            subject = 'Activate Your Account'
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"http://{current_site.domain}/activate/{uid}/{token}/"
            message = render_to_string('shop/account_activation_email.html', {
                'user': user,
                'activation_link': activation_link,
            })
            send_mail(subject, message, None, [user.email])

            return redirect('shop:activation_sent')
    else:
        form = UserRegisterForm()
    return render(request, "shop/signup.html", {"form": form})


def activation_sent(request):
    return render(request, "shop/activation_sent.html")


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect("shop:dashboard")
    else:
        return render(request, "shop/account_activation_invalid.html")


def resend_activation(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                messages.info(request, "Account already active. Please login.")
                return redirect("shop:login")
            else:
                current_site = get_current_site(request)
                subject = "Activate your account"
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                message = render_to_string("shop/account_activation_email.html", {
                    "user": user,
                    "activation_link": f"http://{current_site.domain}/activate/{uid}/{token}/",
                })
                send_mail(subject, message, None, [user.email])
                messages.success(request, "Activation email resent. Check your inbox.")
                return redirect("shop:activation_sent")
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
    return render(request, "shop/resend_activation.html")


@login_required
def update_profile(request):
    if request.method == "POST":
        user = request.user
        username = request.POST.get('username')
        email = request.POST.get('email')

        user.username = username
        user.email = email
        user.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('shop:dashboard')

    return render(request, 'shop/update_profile.html')


def home(request):
    products = Product.objects.all()
    return render(request, 'shop/home.html', {'products': products})


def about(request):
    return render(request, "shop/about.html")


def contact(request):
    return render(request, "shop/contact.html")


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, "shop/product_detail.html", {"product": product})


def _get_cart(request):
    return request.session.setdefault("cart", {})


def _cart_totals(cart):
    subtotal = Decimal('0.00')
    for item in cart.values():
        price = Decimal(str(item.get('price', '0')))
        qty = int(item.get('qty', 0))
        subtotal += price * qty
    return subtotal


def cart_view(request):
    cart = request.session.get('cart', {})
    # Normalize cart items to dict for compatibility
    for key, item in list(cart.items()):
        if isinstance(item, int):
            cart[key] = {'qty': item, 'price': '0'}
        elif not isinstance(item, dict):
            cart[key] = {'qty': 0, 'price': '0'}

    subtotal = _cart_totals(cart)
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)

    cart_items = []
    for product in products:
        item = cart.get(str(product.id), {'qty': 0, 'price': str(product.new_price)})
        qty = int(item.get('qty', 0))
        price = Decimal(str(item.get('price', product.new_price)))
        cart_items.append({
            'product': product,
            'qty': qty,
            'price': price,
            'total': price * qty,
        })

    context = {
        'cart': cart,
        'subtotal': subtotal,
        'cart_items': cart_items,
    }
    return render(request, 'shop/cart.html', context)


def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

    product = get_object_or_404(Product, id=product_id)
    product_id_str = str(product_id)

    if product_id_str in cart:
        if isinstance(cart[product_id_str], dict):
            cart[product_id_str]['qty'] += 1
        else:
            cart[product_id_str] = {'qty': 1, 'price': str(product.new_price)}
    else:
        cart[product_id_str] = {'qty': 1, 'price': str(product.new_price)}

    request.session['cart'] = cart
    return redirect('shop:cart_view')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        messages.success(request, 'Item removed from cart.')
    else:
        messages.warning(request, 'Item not found in cart.')
    return redirect('shop:cart_view')


def update_cart(request, product_id):
    cart = _get_cart(request)
    qty = int(request.POST.get("qty", 1))
    if qty <= 0:
        cart.pop(str(product_id), None)
    else:
        if str(product_id) in cart and isinstance(cart[str(product_id)], dict):
            cart[str(product_id)]["qty"] = qty
        else:
            cart[str(product_id)] = {'qty': qty, 'price': '0'}
    request.session.modified = True
    return redirect("shop:cart_view")


@login_required
def checkout(request):
    cart = _get_cart(request)
    if not cart:
        messages.info(request, "Your cart is empty.")
        return redirect("shop:home")

    if request.method == "POST":
        payment_method = request.POST.get('payment_method')
        bkash_number = request.POST.get('bkash_number', '')

        subtotal = _cart_totals(cart)
        order = Order.objects.create(
            user=request.user,
            total=subtotal,
            payment_method=payment_method,  # jodi model e thake
            bkash_number=bkash_number       # jodi model e thake
        )

        for pk, data in cart.items():
            product = get_object_or_404(Product, id=pk)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=data["qty"],
                price_at_order=product.new_price,
            )
            product.stock -= data["qty"]
            product.save()

        redirect_url = sslcommerz_create_session(order, request)

        if redirect_url:
            request.session["cart"] = {}
            return redirect(redirect_url)
        else:
            messages.error(request, "Payment gateway error. Please try again.")
            return redirect('shop:cart_view')

    # GET request hole checkout page show korbe
    return render(request, 'shop/checkout.html')



@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        post_data = request.POST

        tran_id = post_data.get('tran_id')
        status = post_data.get('status')
        amount = post_data.get('amount')
        currency = post_data.get('currency')

        order = Order.objects.filter(id=tran_id).first()

        if order and status == "VALID" and currency == "BDT" and Decimal(amount) == order.total:
            order.paid = True
            order.save()
            return render(request, 'shop/order_complete.html', {'order': order})
        else:
            messages.error(request, "Payment verification failed.")
            return redirect('shop:cart_view')
    else:
        return HttpResponse("Invalid request method", status=400)


@login_required
def payment_cancel(request):
    messages.warning(request, "Payment cancelled by the user.")
    return redirect('shop:cart_view')


@login_required
def payment_fail(request):
    messages.error(request, "Payment failed or cancelled. Please try again.")
    return redirect("shop:cart_view")


@login_required
def dashboard(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "shop/dashboard.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "shop/order_detail.html", {"order": order})
