from django.shortcuts import render, redirect
from django.contrib import messages
from .models import BuyerUser, Product, Wishlist,Cart
import requests
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import stripe
from django.core.mail import send_mail
from django.conf import settings
import random

YOUR_DOMAIN = 'http://127.0.0.1:8000'
stripe.api_key = settings.STRIPE_PRIVATE_KEY

# Create your views here.
def index(request):
   all_products = Product.objects.all().order_by('-created_at')[:4]
   cart_product_ids = set()
   email = request.session.get('email')
   if email:
      try:
         user = BuyerUser.objects.get(email=email)
         cart_product_ids = set(
            Cart.objects.filter(user=user, payment_status=False).values_list('product_id', flat=True)
         )
      except BuyerUser.DoesNotExist:
         pass
   return render(request, 'index.html', {
      'all_products':     all_products,
      'cart_product_ids': cart_product_ids,
   })

def login(request) :
   if request.method == 'POST':
      email    = request.POST.get('loginemail', '').strip()
      password = request.POST.get('loginpassword', '')

      if not email:
         return render(request, 'login.html', {'error': 'Email is required.'})
      if not password:
         return render(request, 'login.html', {'error': 'Password is required.', 'loginemail': email})

      try:
         user = BuyerUser.objects.get(email=email)
         if user.password == password:
            request.session['email']=user.email
            request.session['firstName']=user.firstName
            if user.profile_picture and user.profile_picture.name:
                request.session['profile_picture'] = user.profile_picture.url
            else:
                request.session['profile_picture'] = None  # or a default image path

            if user.role == "buyer" :
               #messages.success(request, f'Welcome back, {user.firstName}!')
               wishlists=Wishlist.objects.filter(user=user)
               request.session['wishlist_count']=len(wishlists)
               return redirect('index')
            else :
               return redirect('seller_index')
         else:
            return render(request, 'login.html', {'error': 'Incorrect password.', 'loginemail': email})
      except BuyerUser.DoesNotExist:
         return render(request, 'login.html', {'error': 'No account found with this email.', 'loginemail': email})

   return render(request,'login.html')

def signup(request) :
   if request.method == 'POST':
      fname   = request.POST.get('signupfname', '').strip()
      lname   = request.POST.get('signuplname', '').strip()
      email   = request.POST.get('signupemail', '').strip()
      mobile  = request.POST.get('signupmobile', '').strip()
      address = request.POST.get('signupaddress', '').strip()
      password         = request.POST.get('signuppassword', '')
      confirm_password = request.POST.get('signupconfirmpassword', '')

      if BuyerUser.objects.filter(email=email).exists():
         return render(request, 'signup.html', {'email_error': 'This email is already registered.'})

      role = request.POST.get('role', 'buyer')

      if password == confirm_password:
         BuyerUser.objects.create(
            firstName       = fname,
            lastName        = lname,
            mobile          = mobile,
            email           = email,
            address         = address,
            profile_picture = request.FILES.get('profile_picture'),
            password        = password,
            role            = role
         )
         return render(request, 'login.html', {'success': 'Account created successfully! Please login.'})

   return render(request, 'signup.html')

def profile(request):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to view your profile.'})
   try:
      user = BuyerUser.objects.get(email=email)
   except BuyerUser.DoesNotExist:
      return render(request, 'login.html', {'error': 'Session expired. Please login again.'})

   if request.method == 'POST':
      user.firstName = request.POST.get('firstName', '').strip()
      user.lastName  = request.POST.get('lastName', '').strip()
      user.email     = request.POST.get('email', '').strip()
      user.mobile    = request.POST.get('mobile', '').strip()
      user.address   = request.POST.get('address', '').strip()

      new_picture = request.FILES.get('profile_picture')
      if new_picture:
         user.profile_picture = new_picture

      user.save()

      request.session['email']     = user.email
      request.session['firstName'] = user.firstName
      request.session['profile_picture'] = user.profile_picture.url if user.profile_picture else None

      return render(request, 'profile.html', {'user': user, 'success': 'Profile updated successfully!'})

   return render(request, 'profile.html', {'user': user})

def change_password(request):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to change your password.'})
   if request.method == 'POST':
      current_password  = request.POST.get('current_password', '')
      new_password      = request.POST.get('new_password', '')
      confirm_password  = request.POST.get('confirm_password', '')
      try:
         user = BuyerUser.objects.get(email=email)
         if user.password != current_password:
            return render(request, 'change_password.html', {'error': 'Current password is incorrect.'})
         if new_password != confirm_password:
            return render(request, 'change_password.html', {'error': 'New passwords do not match.'})
         user.password = new_password
         user.save()
         del request.session['email']
         del request.session['firstName']
         del request.session['profile_picture']
         msg="User Logged Out Successfully"
        # return render(request,'index.html',{'msg':msg})
         return render(request, 'login.html', {'success': 'Password changed successfully!, Please login agin!'})
      except BuyerUser.DoesNotExist:
         return render(request, 'login.html', {'error': 'Session expired. Please login again.'})
   return render(request, 'change_password.html')

def logout(request):
    try:
        del request.session['email']
        del request.session['firstName']
        del request.session['profile_picture']
        del request.session['wishlist_count']
        del request.session["cart_count"]

    except KeyError:
        pass
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

#display all products added by sellers
def shop(request):
   category     = request.GET.get('category', '').strip()
   all_products = Product.objects.all().order_by('-created_at')
   if category:
      all_products = all_products.filter(category=category)
   cart_product_ids = set()
   email = request.session.get('email')
   if email:
      try:
         user = BuyerUser.objects.get(email=email)
         cart_product_ids = set(
            Cart.objects.filter(user=user, payment_status=False).values_list('product_id', flat=True)
         )
      except BuyerUser.DoesNotExist:
         pass
   return render(request, 'shop.html', {
      'all_products':     all_products,
      'active_category':  category,
      'categories':       ['Men', 'Women', 'Kids', 'Others'],
      'cart_product_ids': cart_product_ids,
   })

#product detail of particular product
def product_detail(request, product_id):
   try:
      product = Product.objects.get(id=product_id)
   except Product.DoesNotExist:
      return redirect('shop')
   related_products = Product.objects.filter(category=product.category).exclude(id=product_id)[:4]
   wishlist_flag = False
   cart_flag     = False
   email = request.session.get('email')
   if email:
      try:
         user = BuyerUser.objects.get(email=email)
         wishlist_flag = Wishlist.objects.filter(user=user, product=product).exists()
         cart_flag     = Cart.objects.filter(user=user, product=product, payment_status=False).exists()
         request.session['wishlist_count'] = Wishlist.objects.filter(user=user).count()
         request.session['cart_count']     = Cart.objects.filter(user=user, payment_status=False).count()
      except BuyerUser.DoesNotExist:
         pass
   return render(request, 'product-single.html', {
      'product':          product,
      'related_products': related_products,
      'wishlist_flag':    wishlist_flag,
      'cart_flag':        cart_flag,
   })

def payment_success(request):
   email = request.session.get('email')
   if not email:
      session_id = request.GET.get('session_id')
      if not session_id:
         return redirect('login')
      try:
         stripe_session = stripe.checkout.Session.retrieve(session_id)
         email = stripe_session.customer_details.email
      except Exception:
         return redirect('login')
   try:
      user = BuyerUser.objects.get(email=email)
   except BuyerUser.DoesNotExist:
      return redirect('login')
   cart_items = Cart.objects.filter(user=user, payment_status=False)
   net_amount = sum(item.total_price for item in cart_items)
   cart_items.update(payment_status=True)
   request.session['cart_count'] = 0
   return render(request, 'success.html', {'net_amount': net_amount})

def payment_cancel(request):
   return render(request, 'cancel.html')

def orders(request):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to view your orders.'})
   user = BuyerUser.objects.get(email=email)
   order_items = Cart.objects.filter(user=user, payment_status=True).select_related('product').order_by('-date')
   return render(request, 'orders.html', {'order_items': order_items})

#cart Functionality
def cart(request):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to view your cart.'})
   user = BuyerUser.objects.get(email=email)
   cart_items = Cart.objects.filter(user=user, payment_status=False).select_related('product')
   net_amount = sum(item.total_price for item in cart_items)
   request.session['cart_count'] = cart_items.count()
   return render(request, 'cart.html', {'cart_items': cart_items, 'net_amount': net_amount})

def add_to_cart(request, product_id):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to add items to your cart.'})
   try:
      product = Product.objects.get(id=product_id)
      user = BuyerUser.objects.get(email=email)
      cart_item = Cart.objects.filter(user=user, product=product, payment_status=False).first()
      if cart_item:
         cart_item.product_qty += 1
         cart_item.total_price = cart_item.product_qty * int(product.price)
         cart_item.save()
      else:
         Cart.objects.create(
            user=user,
            product=product,
            product_price=int(product.price),
            product_qty=1,
            total_price=int(product.price),
            payment_status=False,
         )
      request.session['cart_count'] = Cart.objects.filter(user=user, payment_status=False).count()
   except Product.DoesNotExist:
      pass
   return redirect('product_detail', product_id=product_id)

def remove_frm_cart(request, cart_id):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to manage your cart.'})
   try:
      user = BuyerUser.objects.get(email=email)
      Cart.objects.filter(id=cart_id, user=user).delete()
      request.session['cart_count'] = Cart.objects.filter(user=user, payment_status=False).count()
   except Cart.DoesNotExist:
      pass
   return redirect('cart')

#checkout and payment
def create_checkout_session(request):
   email = request.session.get('email')
   if not email:
      return redirect('login')
   user = BuyerUser.objects.get(email=email)
   cart_items = Cart.objects.filter(user=user, payment_status=False).select_related('product')
   if not cart_items.exists():
      return redirect('cart')
   line_items = []
   for item in cart_items:
      line_items.append({
         'price_data': {
            'currency': 'inr',
            'unit_amount': item.product_price * 100,
            'product_data': {
               'name': item.product.product_name,
            },
         },
         'quantity': item.product_qty,
      })
   customer = stripe.Customer.create(
      name=f"{user.firstName} {user.lastName}",
      email=user.email,
   )
   session = stripe.checkout.Session.create(
      payment_method_types=['card'],
      line_items=line_items,
      mode='payment',
      customer=customer.id,
      billing_address_collection='required',
      success_url=YOUR_DOMAIN + '/payment-success/?session_id={CHECKOUT_SESSION_ID}',
      cancel_url=YOUR_DOMAIN + '/payment-cancel/',
   )
   return redirect(session.url)

#wishlist functionality
def wishlist(request) :
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to view your wishlist.'})
   user = BuyerUser.objects.get(email=email)
   wishlist_items = Wishlist.objects.filter(user=user).select_related('product')
   request.session['wishlist_count'] = wishlist_items.count()
   return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

def add_to_whishlist(request, product_id) :
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to add items to your wishlist.'})
   try:
      product = Product.objects.get(id=product_id)
      user = BuyerUser.objects.get(email=email)
      Wishlist.objects.get_or_create(user=user, product=product)
      request.session['wishlist_count'] = Wishlist.objects.filter(user=user).count()
   except Product.DoesNotExist:
      pass
   return redirect('product_detail', product_id=product_id)

def remove_from_whishlist(request, product_id) :
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to manage your wishlist.'})
   try:
      product = Product.objects.get(id=product_id)
      user = BuyerUser.objects.get(email=email)
      Wishlist.objects.filter(user=user, product=product).delete()
      request.session['wishlist_count'] = Wishlist.objects.filter(user=user).count()
   except Product.DoesNotExist:
      pass
   next_page = request.GET.get('next', 'product')
   if next_page == 'wishlist':
      return redirect('wishlist')
   return redirect('product_detail', product_id=product_id)

def change_qty(request, product_id):
    email = request.session.get('email')
    if not email:
        return redirect('login')
    if request.method == 'POST':
        try:
            user     = BuyerUser.objects.get(email=email)
            cart     = Cart.objects.get(product_id=product_id, user=user, payment_status=False)
            qty      = int(request.POST.get('product_qty', 1))
            if qty < 1:
                qty = 1
            cart.product_qty = qty
            cart.total_price = cart.product_price * qty
            cart.save()
            request.session['cart_count'] = Cart.objects.filter(user=user, payment_status=False).count()
        except (Cart.DoesNotExist, ValueError):
            pass
    return redirect('cart')


#Seller 
def seller_index(request):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to access the seller dashboard.'})

   try:
      seller = BuyerUser.objects.get(email=email)
   except BuyerUser.DoesNotExist:
      return render(request, 'login.html', {'error': 'Session expired. Please login again.'})

   all_products  = Product.objects.filter(seller=seller).order_by('-created_at')
   total         = all_products.count()
   recent        = all_products[:8]

   cat_counts = {
      'Men':    all_products.filter(category='Men').count(),
      'Women':  all_products.filter(category='Women').count(),
      'Kids':   all_products.filter(category='Kids').count(),
      'Others': all_products.filter(category='Others').count(),
   }

   return render(request, 'seller/seller-index.html', {
      'recent':     recent,
      'total':      total,
      'cat_counts': cat_counts,
      'seller':     seller,
   })

def seller_change_password(request) : 
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to change your password.'})
   if request.method == 'POST':
      current_password  = request.POST.get('current_password', '')
      new_password      = request.POST.get('new_password', '')
      confirm_password  = request.POST.get('confirm_password', '')
      try:
         user = BuyerUser.objects.get(email=email)
         if user.password != current_password:
            return render(request, 'seller/seller-change-password.html', {'error': 'Current password is incorrect.'})
         if new_password != confirm_password:
            return render(request, 'seller/seller-change-password.html', {'error': 'New passwords do not match.'})
         user.password = new_password
         user.save()
         del request.session['email']
         del request.session['firstName']
         del request.session['profile_picture']
         msg="User Logged Out Successfully"
        # return render(request,'index.html',{'msg':msg})
         return render(request, 'login.html', {'success': 'Password changed successfully!, Please login agin!'})
      except BuyerUser.DoesNotExist:
         return render(request, 'login.html', {'error': 'Session expired. Please login again.'})
   return render(request, 'change_password.html')

def seller_profile(request) : 
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to view your profile.'})
   try:
      user = BuyerUser.objects.get(email=email)
   except BuyerUser.DoesNotExist:
      return render(request, 'login.html', {'error': 'Session expired. Please login again.'})

   if request.method == 'POST':
      user.firstName = request.POST.get('firstName', '').strip()
      user.lastName  = request.POST.get('lastName', '').strip()
      user.email     = request.POST.get('email', '').strip()
      user.mobile    = request.POST.get('mobile', '').strip()
      user.address   = request.POST.get('address', '').strip()

      new_picture = request.FILES.get('profile_picture')
      if new_picture:
         user.profile_picture = new_picture

      user.save()

      request.session['email']     = user.email
      request.session['firstName'] = user.firstName
      request.session['profile_picture'] = user.profile_picture.url if user.profile_picture else None

      return render(request, 'seller/seller-profile.html', {'user': user, 'success': 'Profile updated successfully!'})

   return render(request, 'seller/seller-profile.html', {'user': user})

#displaying products added by logged in seller
def seller_products(request):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to view your products.'})

   try:
      seller = BuyerUser.objects.get(email=email)
   except BuyerUser.DoesNotExist:
      return render(request, 'login.html', {'error': 'Session expired. Please login again.'})

   all_products = Product.objects.filter(seller=seller).order_by('-created_at')
   total_count  = all_products.count()

   active_category = request.GET.get('category', '').strip()
   if active_category:
      products = all_products.filter(category=active_category)
   else:
      products = all_products

   cat_choices = [('Men', 'Men'), ('Women', 'Women'), ('Kids', 'Kids'), ('Others', 'Others')]
   categories  = [(cat, label, all_products.filter(category=cat).count()) for cat, label in cat_choices]

   return render(request, 'seller/seller-products.html', {
      'products':        products,
      'total_count':     total_count,
      'categories':      categories,
      'active_category': active_category,
   })

def add_product(request):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to add a product.'})

   if request.method == 'POST':
      category      = request.POST.get('category', '').strip()
      product_name  = request.POST.get('product_name', '').strip()
      price         = request.POST.get('price', '').strip()
      description   = request.POST.get('description', '').strip()
      product_image = request.FILES.get('product_image')

      if not all([category, product_name, price, description, product_image]):
         messages.error(request, 'All fields are required.')
         return render(request, 'seller/seller-add-product.html')

      try:
         seller = BuyerUser.objects.get(email=email)
         Product.objects.create(
            seller        = seller,
            category      = category,
            product_name  = product_name,
            price         = price,
            description   = description,
            product_image = product_image,
         )
         messages.success(request, 'Product added successfully!')
         return redirect(seller_index)
      except BuyerUser.DoesNotExist:
         return render(request, 'login.html', {'error': 'Session expired. Please login again.'})

   return render(request, 'seller/seller-add-product.html')

def edit_product(request, product_id):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to edit a product.'})

   try:
      seller  = BuyerUser.objects.get(email=email)
      product = Product.objects.get(id=product_id, seller=seller)
   except BuyerUser.DoesNotExist:
      return render(request, 'login.html', {'error': 'Session expired. Please login again.'})
   except Product.DoesNotExist:
      messages.error(request, 'Product not found or you do not have permission to edit it.')
      return redirect('seller_products')

   if request.method == 'POST':
      category     = request.POST.get('category', '').strip()
      product_name = request.POST.get('product_name', '').strip()
      price        = request.POST.get('price', '').strip()
      description  = request.POST.get('description', '').strip()
      new_image    = request.FILES.get('product_image')

      if not all([category, product_name, price, description]):
         messages.error(request, 'All fields except image are required.')
         return render(request, 'seller/seller-edit-product.html', {'product': product})

      product.category     = category
      product.product_name = product_name
      product.price        = price
      product.description  = description
      if new_image:
         product.product_image = new_image
      product.save()

      messages.success(request, 'Product updated successfully!')
      return redirect('seller_products')

   return render(request, 'seller/seller-edit-product.html', {'product': product})

def delete_product(request, product_id):
   email = request.session.get('email')
   if not email:
      return render(request, 'login.html', {'error': 'Please login to delete a product.'})

   if request.method == 'POST':
      try:
         seller  = BuyerUser.objects.get(email=email)
         product = Product.objects.get(id=product_id, seller=seller)
         product.delete()
         messages.success(request, 'Product deleted successfully.')
      except Product.DoesNotExist:
         messages.error(request, 'Product not found or you do not have permission to delete it.')

   return redirect('seller_products')

def forgot_password(request):
   if request.method == 'POST':
      email = request.POST.get('email', '').strip()
      if BuyerUser.objects.filter(email=email).exists():
         otp = random.randint(1000, 9999)
         subject = "Forgot Password OTP - Winkle"
         message = f"Your OTP for password reset is: {otp}\n\nThis OTP is valid for this session only."
         send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
         request.session['reset_email'] = email
         request.session['otp'] = otp
         return redirect('verify_otp')
      return render(request, 'forgot_password.html', {'error': 'No account found with this email.'})
   return render(request, 'forgot_password.html')

def verify_otp(request):
   if not request.session.get('reset_email'):
      return redirect('forgot_password')
   if request.method == 'POST':
      entered = request.POST.get('otp', '').strip()
      if str(request.session.get('otp')) == entered:
         return redirect('reset_password')
      return render(request, 'verify_otp.html', {'error': 'Invalid OTP. Please try again.'})
   return render(request, 'verify_otp.html')

def reset_password(request):
   email = request.session.get('reset_email')
   if not email:
      return redirect('forgot_password')
   if request.method == 'POST':
      new_password     = request.POST.get('new_password', '')
      confirm_password = request.POST.get('confirm_password', '')
      if not new_password:
         return render(request, 'reset_password.html', {'error': 'Password cannot be empty.'})
      if new_password != confirm_password:
         return render(request, 'reset_password.html', {'error': 'Passwords do not match.'})
      user = BuyerUser.objects.get(email=email)
      user.password = new_password
      user.save()
      del request.session['reset_email']
      return render(request, 'login.html', {'success': 'Password reset successfully! Please login.'})
   return render(request, 'reset_password.html')

def contact(request) :
   return render(request,'contact.html')

def about(request) :
   return render(request,'about.html')

def blog(request) :
   return render(request,'blog.html')

def single_blog(request) :
   return render(request,'blog-single.html')