from django.contrib import admin
from .models import User, Shop, UserType, Order, OrderProduct, Product, ProductCategory, ExtraParameter, Basket, BasketProduct

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff')

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'accepting_status', 'url')
    search_fields = ('name',)

@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ('type',)
    search_fields = ('type',)


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'total_price', 'status')
    list_filter = ('status',)
    search_fields = ('user__email',)
    inlines = [OrderProductInline,]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'model', 'product_quantity', 'shop')
    search_fields = ('name', 'model')
    list_filter = ('shop',)

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ExtraParameter)
class ExtraParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'product')
    search_fields = ('name', 'product__name')

@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__email',)

@admin.register(BasketProduct)
class BasketProductAdmin(admin.ModelAdmin):
    list_display = ('basket', 'product', 'quantity')
    search_fields = ('basket__user__email', 'product__name')