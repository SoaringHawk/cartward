"""cartward URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.urls import path, include
from users import views as user_views
from orders import views as order_views
from django.contrib.auth import views as auth_views
from django.conf.urls import url

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.home, name='home-page'),
    path('signin-register/', user_views.signinregister, name='signin-register'),
    path('activate/<uidb64>/<token>/', user_views.activate, name='activate'),
    path('signin-register/resend/<int:pk>/', user_views.resend, name='resend-register'),
    path('logout/', user_views.logout_view, name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html',
                                                     success_url='/signin-register/'), name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),
    path('US/search/', order_views.search, name='search-page'),
    path('US/product/<slug:slug>/', order_views.product, name='product-page'),
    path('US/search/<slug:query_slug>/<slug:page_slug>/', order_views.list, name='list-page'),
    url(r'^add_to_cart/$', order_views.add_to_cart, name='add_to_cart-method'),
    url(r'^update_cart/$', order_views.update_cart),
    url(r'^get_shipping/$', order_views.get_shipping),
    url(r'^delete_item/$', order_views.delete_item),
    url(r'^get_item_number/$', order_views.get_item_number),
    url(r'^get_pages/$', order_views.query_page),
    url(r'^get_prohibited/$', order_views.get_prohibited_item),
    url(r'^save_shipping/$', order_views.save_shipping),
    path('cart/', order_views.get_cart, name='cart-page'),
    path('checkout/', order_views.checkout, name='checkout-page'),
    path('order/', order_views.place_order, name='order-page'),
    path('profile/', user_views.profile, name='profile-page'),
    path('change_password/', user_views.change_password, name='change-password-page'),
    path('orders/', user_views.orders, name='orders-page'),
    path('orderdetails/<int:pk>/', user_views.orderdetails, name='orderdetails-page'),
    path('deposit/', user_views.deposit, name='deposit-page'),
    path('wishlist/', order_views.wishlist, name='wishlist-page'),
    path('termsandconditions/', user_views.termandcondition, name='tandc-page'),
    path('privacypolicy/', user_views.privacypolicy, name='privacy-page'),
    path('contact-us/', user_views.contactus, name='contact-page'),
    path('about-us/', user_views.aboutus, name='aboutus-page'),
    path('prohibited-item/', order_views.prohibited, name='prohibited-page'),


]
