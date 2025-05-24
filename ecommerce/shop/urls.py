from django.urls import path
from django.contrib.auth import views as auth_views
from .views import CustomLoginView, CustomLogoutView
from . import views

app_name = "shop"

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    # Cart routes
    path("cart/", views.cart_view, name="cart_view"),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path("cart/update/<int:product_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),

    # Checkout & Payment
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-fail/', views.payment_fail, name='payment_fail'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),  # If implemented


    # User Registration & Activation
    path('register/', views.register, name='register'),
    path("activation_sent/", views.activation_sent, name="activation_sent"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    path("resend_activation/", views.resend_activation, name="resend_activation"),

    # Login / Logout
    path('accounts/login/', auth_views.LoginView.as_view(template_name='shop/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='shop/logout.html'), name='logout'),

    # Password Reset flow
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(template_name='shop/password_reset_form.html'), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='shop/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='shop/password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='shop/password_reset_complete.html'), name='password_reset_complete'),
]
