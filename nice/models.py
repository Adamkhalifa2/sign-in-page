from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=20)
    pdescription = models.CharField(max_length=200)  # Corrected typo in field name
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Corrected typo in parameter name
    pimage = models.ImageField(upload_to='images/')  # Corrected typo in parameter name

    def __str__(self):
        return self.name


class Item(models.Model):  # Changed Items to Item for better naming convention
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.quantity} x {self.product.name} {self.pimage} {self. pdescription}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.user.username