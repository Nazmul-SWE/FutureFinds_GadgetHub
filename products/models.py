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
    PRODUCT_TYPE_CHOICES = [
        ('regular', 'Regular Product'),
        ('preorder', 'Pre-order Product'),
        ('flash_sale', 'Flash Sale Product'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True)
    preorder_product = models.ForeignKey('PreOrderProduct', on_delete=models.CASCADE, blank=True, null=True)
    flash_sale_product = models.ForeignKey('FlashSaleProduct', on_delete=models.CASCADE, blank=True, null=True)
    product_type = models.CharField(
        choices=PRODUCT_TYPE_CHOICES, 
        default='regular', 
        max_length=20
    )
    quantity = models.PositiveIntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')

    class Meta:
        unique_together = ('user', 'product_type', 'product', 'preorder_product', 'flash_sale_product')

    def __str__(self):
        if self.product_type == 'regular' and self.product:
            return f"{self.quantity} of {self.product.name}"
        elif self.product_type == 'preorder' and self.preorder_product:
            return f"{self.quantity} of {self.preorder_product.name}"
        elif self.product_type == 'flash_sale' and self.flash_sale_product:
            return f"{self.quantity} of {self.flash_sale_product.name}"
        return f"{self.quantity} of unknown product"

    def get_total_price(self):
        if self.product_type == 'regular' and self.product:
            return self.quantity * self.product.price
        elif self.product_type == 'preorder' and self.preorder_product:
            return self.quantity * self.preorder_product.price
        elif self.product_type == 'flash_sale' and self.flash_sale_product:
            return self.quantity * self.flash_sale_product.get_sale_price()
        return 0


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


class FlashSaleProduct(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='flash_sale_images/', blank=True, null=True)
    discount_type = models.CharField(
        max_length=10,
        choices=[('percent', 'Percent'), ('fixed', 'Fixed')],
        default='percent'
    )
    original_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Enter percentage for percent discount, or fixed amount for fixed discount"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def get_sale_price(self):
        if self.discount_type == 'percent':
            sale_price = self.original_price * (1 - self.discount_value / 100)
        else:  # fixed
            sale_price = self.original_price - self.discount_value
        return int(sale_price)


class PreOrderProduct(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='preorder_images/', blank=True, null=True)
    expected_release_date = models.DateField()
    preorder_start_date = models.DateTimeField()
    preorder_end_date = models.DateTimeField()
    max_preorder_quantity = models.PositiveIntegerField(default=100)
    current_preorders = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_preorder_available(self):
        now = timezone.now()
        return (self.is_active and
                self.preorder_start_date <= now <= self.preorder_end_date and
                self.current_preorders < self.max_preorder_quantity)

    def preorder_slots_remaining(self):
        return self.max_preorder_quantity - self.current_preorders

    def __str__(self):
        return self.name


class PreOrderItem(models.Model):
    preorder_product = models.ForeignKey(PreOrderProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preorder_carts')

    def __str__(self):
        return f"{self.quantity} of {self.preorder_product.name}"

    def get_total_price(self):
        return self.quantity * self.preorder_product.price


class PreOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="preorders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Fulfilled", "Fulfilled"),
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
        return f"PreOrder {self.id} by {self.user.username}"


class PreOrderOrderItem(models.Model):
    preorder = models.ForeignKey(PreOrder, on_delete=models.CASCADE, related_name="items")
    preorder_product = models.ForeignKey(PreOrderProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.preorder_product.name} in PreOrder {self.preorder.id}"


class FlashSaleOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flash_sale_orders')
    product = models.ForeignKey(FlashSaleProduct, on_delete=models.CASCADE, related_name='flash_sale_orders')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Confirmed', 'Confirmed'),
            ('Delivered', 'Delivered'),
            ('Cancelled', 'Cancelled'),
        ],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FlashSaleOrder {self.id} by {self.user.username}"

    def get_total_price(self):
        return self.quantity * self.price
