from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Shop, Basket, Product


# admin.site.register(User , UserAdmin)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "address", "shop"]


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "url", "user"]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "model"]


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ["id", "user"]