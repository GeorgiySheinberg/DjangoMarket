from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    address = models.CharField(max_length=200, null=True, blank=True)
    shop = models.OneToOneField('Shop', on_delete=models.CASCADE, null=True, blank=True)
    type = models.ForeignKey('UserType', on_delete=models.CASCADE, default=2)
    objects = UserManager()

    USERNAME_FIELD = 'email'  # Используем email как уникальное поле
    REQUIRED_FIELDS = []  # Указываем, что username не требуется

class Shop(models.Model):
    name = models.CharField(max_length=100)
    accepting_status = models.BooleanField(default=False)
    url = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class UserType(models.Model):
    type = models.CharField(max_length=30)

    def __str__(self):
        return self.type
class Order(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='order')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_address = models.CharField(max_length=200, null=True, blank=True)
    product = models.ManyToManyField('Product', related_name='order', blank=True, through="OrderProduct")
    status = models.CharField(max_length=30)
    def __str__(self):
        return str(self.user)


class OrderProduct(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='order_products')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='order_products')
    quantity = models.IntegerField()

    def __str__(self):
        return str(self.order)


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    model = models.CharField(max_length=100)
    product_quantity = models.IntegerField()

    category = models.ForeignKey('ProductCategory', on_delete=models.PROTECT, related_name='product')
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, null=False)


class ExtraParameter(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='extra_parameters')

    def __str__(self):
        return self.name


class Basket(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='basket')
    product = models.ManyToManyField(Product, related_name='basket', through="BasketProduct")


class BasketProduct(models.Model):
    basket = models.ForeignKey(Basket,   on_delete=models.CASCADE,  related_name='position')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='position')
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ('basket', 'product')