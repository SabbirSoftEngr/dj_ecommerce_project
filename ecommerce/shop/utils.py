import requests
from decimal import Decimal

def sslcommerz_create_session(order, request):
    store_id = 'mysho682be5a26ca62'  # Apnar Store ID
    store_passwd = 'mysho682be5a26ca62@ssl'  # Apnar Store Password (API Secret)
    is_live = False  # Sandbox mode False, live True

    if is_live:
        api_url = 'https://securepay.sslcommerz.com/gwprocess/v3/api.php'
    else:
        api_url = 'https://sandbox.sslcommerz.com/gwprocess/v3/api.php'

    post_data = {
        'store_id': store_id,
        'store_passwd': store_passwd,
        'total_amount': str(order.total),
        'currency': 'BDT',
        'tran_id': str(order.id),
        'success_url': request.build_absolute_uri('/payment-success/'),
        'fail_url': request.build_absolute_uri('/payment-fail/'),
        'cancel_url': request.build_absolute_uri('/payment-cancel/'),
        'emi_option': 0,
        'cus_name': request.user.username,
        'cus_email': request.user.email,
        'cus_add1': request.user.profile.address if hasattr(request.user, 'profile') else '',
        'cus_phone': request.user.profile.phone if hasattr(request.user, 'profile') else '',
        'shipping_method': 'NO',
        'num_of_item': order.items.count() if hasattr(order, 'items') else 1,
        'product_name': 'Order #' + str(order.id),
        'product_category': 'Ecommerce',
        'product_profile': 'general',
    }

    try:
        response = requests.post(api_url, data=post_data)
        response_data = response.json()
        if response_data.get('status') == 'SUCCESS':
            return response_data.get('GatewayPageURL')
        else:
            print('SSLCommerz API error:', response_data)
            return None
    except Exception as e:
        print('Exception during SSLCommerz session creation:', e)
        return None
