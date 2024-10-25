from djoser.serializers import UserCreateSerializer, UserSerializer

from .models import Product, ExtraParameter, BasketProduct, OrderProduct, User

from rest_framework import serializers


class MarketUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'password')


class MarketUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'address')


class ExtraParametersSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtraParameter
        fields = ['name', 'value']


class ProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['id', 'name', 'model', 'product_quantity', 'price']


class DetailedProductSerializer(serializers.ModelSerializer):
    extra_parameters = ExtraParametersSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'model', 'product_quantity', 'price', 'extra_parameters']


class ProductsSerializer(serializers.ModelSerializer):

    class Meta:

        model = Product

        fields = ['id','name', 'price']



class BasketProductSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    product = ProductsSerializer()

    class Meta:
        model = BasketProduct
        fields = ['id', 'basket', 'product', 'quantity', 'total_price']

    def get_total_price(self, obj) -> float:
        return obj.product.price * obj.quantity



class BasketProductCreateSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = BasketProduct
        fields = ['id', 'basket', 'product', 'quantity']

    def create(self, validated_data):

        basket_product = BasketProduct.objects.create(
            basket_id=validated_data.get('basket').pk,
            product_id=validated_data.get('product').pk,
            quantity=validated_data.get('quantity')
        )
        return basket_product


class OrderProductSerializer(serializers.ModelSerializer):
    product = ProductsSerializer(read_only=True)
    class Meta:
        model = OrderProduct
        fields = ('id', 'order', 'product', 'quantity')
        read_only_fields = ('id',)