from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name="index"),
    #auth
    path('login/',views.login,name="login"),
    path('signup/',views.signup,name="signup"),
    path('logout/', views.logout, name='logout'),
    
    #contact,about,blog
    path('contact/',views.contact,name="contact"),
    path('blog/',views.blog,name="blog"),
    path('about/',views.about,name="about"),
    path('single_blog/',views.single_blog,name="single_blog"),

    #profile_changePassword
    path('profile/', views.profile, name='profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    
    #product list, single product detail
    path('shop/', views.shop, name='shop'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    #cart
    path('cart/', views.cart, name="cart"),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:cart_id>/', views.remove_frm_cart, name='remove_frm_cart'),
    path('change-qty/<int:product_id>/',views.change_qty,name="change-qty"),

    #checkout-payment
    path('create-checkout-session/', views.create_checkout_session, name='payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('orders/', views.orders, name='orders'),

    #wishlist
    path('wishlist/',views.wishlist,name = 'wishlist'),
    path('add-to-wishlist/<int:product_id>/',views.add_to_whishlist,name='add_to_whishlist'),
    path('remove-from-wishlist/<int:product_id>/',views.remove_from_whishlist,name='remove_from_whishlist'),
    
    #seller index, profile, change password
    path('seller/', views.seller_index, name='seller_index'),
    path('seller/seller-profile',views.seller_profile,name="seller_profile"),
    path('seller/seller-change-password',views.seller_change_password,name="seller_change_password"),
    
    #all products, add-update-delete-update product
    path('seller/add-product/', views.add_product, name='add_product'),
    path('seller/all-products/', views.seller_products, name='seller_products'),
    path('seller/edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('seller/delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    
]   
