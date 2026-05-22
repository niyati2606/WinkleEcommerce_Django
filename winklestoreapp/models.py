from django.db import models
from django.utils import timezone

# Create your models here.
class BuyerUser(models.Model) :
    ROLE_CHOICES = [
        ('buyer',  'Buyer'),
        ('seller', 'Seller'),
    ]
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    email = models.EmailField()
    mobile = models.PositiveIntegerField()
    address = models.TextField()
    password = models.CharField()
    profile_picture = models.ImageField(upload_to="profile_picture/", null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')

    def __str__(self):
        return self.firstName + " " +self.lastName


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Men',    'Men'),
        ('Women',  'Women'),
        ('Kids',   'Kids'),
        ('Others', 'Others'),
    ]
    seller       = models.ForeignKey(BuyerUser, on_delete=models.CASCADE)
    category     = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    product_name = models.CharField(max_length=200)
    price        = models.DecimalField(max_digits=10, decimal_places=2)
    description  = models.TextField()
    product_image = models.ImageField(upload_to='products/')
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.seller.firstName + " " + self.product_name
    
class Wishlist(models.Model):
    user=models.ForeignKey(BuyerUser,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    date=models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.firstName+" - "+self.product.product_name

class Cart(models.Model):
    user=models.ForeignKey(BuyerUser,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    date=models.DateTimeField(default=timezone.now)
    product_price=models.PositiveIntegerField()
    product_qty=models.PositiveIntegerField(default=1)
    total_price=models.PositiveIntegerField()
    payment_status=models.BooleanField(default=False)

    def __str__(self):
        return self.user.firstName+" - "+self.product.product_name