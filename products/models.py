from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, blank=True, null=True)
    slug = models.SlugField(unique=True)
    category_image = models.ImageField(upload_to='category_images/', blank=True, null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True)


    def __str__(self):
        return self.name

class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

    def get_total_price(self):
        return self.quantity * self.product.price


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    PAYMENT_CHOICES = [
        ("SSLCommerz", "SSLCommerz"),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default="SSLCommerz")

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Order {self.order.id}"



class ProductRent(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='rental_products/')
    rent_price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=1)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.title

class RentalOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_orders')
    product = models.ForeignKey(ProductRent, on_delete=models.CASCADE, related_name='rental_orders')
    rental_start_date = models.DateField()
    rental_end_date = models.DateField()
    total_rent_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Confirmed', 'Confirmed'),
            ('Returned', 'Returned'),
            ('Cancelled', 'Cancelled'),
        ],
        default='Pending'
    )

    def clean(self):
        if self.rental_end_date <= self.rental_start_date:
            raise ValidationError("Rental end date must be after the start date.")

    def save(self, *args, **kwargs):
        rental_days = (self.rental_end_date - self.rental_start_date).days
        self.total_rent_price = rental_days * self.product.rent_price_per_day

        if self.status == 'Confirmed' and self.product.stock > 0:
            self.product.stock -= 1
            self.product.save()

        if self.status == 'Returned':
            self.product.stock += 1
            self.product.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rental Order {self.id} by {self.user.username}"


class RentalOrderItem(models.Model):
    rental_order = models.ForeignKey(RentalOrder, on_delete=models.CASCADE, related_name='rental_items')
    product = models.ForeignKey(ProductRent, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    rent_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.title} in Rental Order {self.rental_order.id}"



