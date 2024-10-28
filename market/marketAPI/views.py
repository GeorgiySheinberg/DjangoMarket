from itertools import product

from django.shortcuts import render

import yaml
import logging
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import render

from rest_framework import viewsets, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProductCategory, Product, ExtraParameter, BasketProduct, OrderProduct, Order, UserType, \
    Basket, Shop
from .serializer import DetailedProductSerializer, BasketProductSerializer, \
    OrderProductSerializer, ProductSerializer, BasketProductCreateSerializer, MarketUserSerializer

import environ

from .tasks import send_order_confirmation_to_suppliers, send_order_confirmation_email

logger = logging.getLogger(__name__)
env = environ.Env()
environ.Env.read_env()

class UpdateUserAddressView(APIView):
    """
        Обновление адреса пользователя.

        Этот класс представляет собой представление для обновления адреса пользователя.
        Он использует частичное обновление (PATCH) и требует аутентификации.

        Атрибуты:
            serializer_class (MarketUser Serializer): Сериализатор для валидации и
                сохранения данных пользователя.
            permission_classes (list): Список классов разрешений, требуемых для доступа
                к этому представлению. В данном случае требуется аутентификация.

        Методы:
            patch(request): Обрабатывает PATCH-запрос для частичного обновления
                данных пользователя. Ожидает данные в формате JSON и обновляет только те поля, которые были переданы в запросе.
        """
    serializer_class = MarketUserSerializer
    permission_classes = [IsAuthenticated]
    def patch(self, request):
        """
        Обрабатывает PATCH-запрос для обновления адреса пользователя.

        Параметры:
            request (Request): Объект запроса, содержащий данные для обновления пользователя.

        Возвращает:
            Response: Ответ с сериализованными данными пользователя при успешном обновлении, или ошибками валидации с кодом состояния 400 при
            неудаче.
        """
        user = request.user
        serializer = MarketUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class PartnerUpdateView(GenericAPIView):
    """
    Представление для обновления данных партнера.

    Этот класс предназначен для обработки POST-запросов, которые позволяют
    загружать и обновлять данные о товарах и категориях из YAML-файла.
    Доступ к этому представлению ограничен пользователями с определенным типом.

    Атрибуты:
        logger (Logger): Логгер для записи ошибок и информации о процессе.

    Методы:
        post(request): Обрабатывает POST-запрос для загрузки и обновления данных о товарах и категориях из предоставленного YAML-файла.
    """

    logger = logging.getLogger(__name__)
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Обрабатывает POST-запрос для обновления данных о товарах и категориях.

        Параметры:
            request (Request): Объект запроса, содержащий файл YAML с данными
            о товарах и категориях.

        Возвращает:
            JsonResponse: Ответ с информацией о статусе операции. В случае
            успешного выполнения возвращает {'Status': 'OK'}. В случае ошибки
            возвращает объект JsonResponse с соответствующим сообщением и кодом состояния.
        """
        if request.user.type_id == UserType.objects.get(type="customer").id:
            return JsonResponse({'Status': False, 'Error': 'Shop only'}, status=403)

        file = request.data.get('file')
        if not file:
            return JsonResponse({'Status': False, 'Error': 'No file provided'}, status=400)

        try:
            data = yaml.safe_load(file.read())
        except Exception as e:
            logger.error(f"Error loading YAML: {e}")
            return JsonResponse({'Status': False, 'Error': 'Invalid YAML file'}, status=400)

        shop_id = request.user.shop.id

        for category in data.get('categories'):
            ProductCategory.objects.update_or_create(
                id=category.get('id'),
                name=category.get('name')
            )
        for good in data.get('goods'):
            Product.objects.update_or_create(
                id=good.get('id'),
                model=good.get('model'),
                name=good.get('name'),
                price=good.get('price'),
                product_quantity=good.get('quantity'),
                category_id=good.get('category'),
                shop_id=shop_id
            )
            for parameter, value in good.get('parameters').items():
                ExtraParameter.objects.update_or_create(
                    name=parameter,
                    value=value,
                    product_id=good.get('id')
                )

        return JsonResponse({'Status': 'OK'})

class ProductView(GenericAPIView):
    """
    Представление для получения списка продуктов или деталей конкретного продукта.

    Этот класс обрабатывает GET-запросы для получения данных о продуктах.
    В зависимости от наличия параметра `pk` в URL, он возвращает либо список всех продуктов, либо детали конкретного продукта.

    Методы:
        get_serializer_class(): Определяет, какой сериализатор использовать
        в зависимости от наличия параметра `pk`.
        get(request, pk=None): Обрабатывает GET-запрос для получения данных о продуктах.
    """
    def get_serializer_class(self):
        """
        Определяет сериализатор для использования в зависимости от наличия параметра `pk`.

        Возвращает:
            class: Сериализатор для списка продуктов (ProductSerializer) или
            сериализатор для конкретного продукта (DetailedProductSerializer).
        """
        if self.kwargs.get('pk') is None:
            return ProductSerializer  # Сериализатор для списка продуктов
        return DetailedProductSerializer  # Сериализатор для конкретного продукта

    def get(self, request, pk=None):
        """
        Обрабатывает GET-запрос для получения данных о продуктах.

        Параметры:
            request (Request): Объект запроса.
            pk (int, optional): Идентификатор конкретного продукта. Если не указан,
            возвращается список всех продуктов.

        Возвращает:
            Response: Ответ с сериализованными данными о продуктах. Если `pk` не указан,
            возвращает список всех продуктов (с фильтрацией по магазинам, которые принимают заказы).
            Если `pk` указан, возвращает детали конкретного продукта.
        """
        if pk is None:
            products = Product.objects.filter(shop__accepting_status=True)
            serializer = self.get_serializer_class()(products, many=True)
        else:
            product = Product.objects.get(pk=pk)
            serializer = self.get_serializer_class()(product)
        return Response(serializer.data)


class BasketProductViewSet(viewsets.GenericViewSet):
    """
    Представление для управления продуктами в корзине пользователя.

    Этот класс предоставляет методы для получения списка продуктов в корзине,
    создания новых продуктов в корзине и обновления существующих продуктов.

    Атрибуты:
        queryset (QuerySet): Набор запросов для получения всех продуктов в корзине.
        serializer_class (Serializer): Сериализатор для работы с продуктами в корзине.

    Методы:
        list(request): Возвращает список всех продуктов в корзине.
        create(request): Создает новый продукт в корзине.
        update(request, *args, **kwargs): Обновляет существующий продукт в корзине.
    """
    queryset = BasketProduct.objects.all()
    serializer_class = BasketProductSerializer

    def list(self, request):
        """
        Обрабатывает GET-запрос для получения списка продуктов в корзине.

        Параметры:
            request (Request): Объект запроса.

        Возвращает:
            Response: Ответ с сериализованными данными о продуктах в корзине.

        """
        basket = getattr(request.user, 'basket', None)

        if basket is None:
            return Response([], status=status.HTTP_200_OK)

        # Получаем продукты в корзине
        queryset = self.queryset.filter(basket=basket)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        """
        Обрабатывает POST-запрос для создания нового продукта в корзине.

        Параметры:
            request (Request): Объект запроса, содержащий данные о новом продукте.

        Возвращает:
            Response: Ответ с сериализованными данными о созданном продукте
            и статусом 201, если создание прошло успешно. В противном случае возвращает ошибки валидации и статус 400.
        """
        user = request.user
        basket = Basket.objects.get_or_create(
            user_id=user.id
        )
        request.data["basket"] = basket[0].pk
        serializer = BasketProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def update(self, request, *args, **kwargs):
        """
       Обрабатывает PATCH-запрос для обновления существующего продукта в корзине.

       Параметры:
           request (Request): Объект запроса, содержащий данные для обновления продукта.
           *args: Дополнительные аргументы.
           **kwargs: Ключевые аргументы, содержащие идентификатор продукта.

       Возвращает:
           Response: Ответ с информацией об обновленном продукте и статусом 200,
           если обновление прошло успешно. В противном случае возвращает ошибки валидации и статус 400.
       """
        basket_product = self.get_object()
        serializer = self.get_serializer(basket_product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'position created': serializer.data})
        return Response(serializer.errors, status=400)


class OrderProductModelViewSet(viewsets.ModelViewSet):
    """
        Обработчик для управления заказами продуктов.

        Этот класс предоставляет методы для создания, чтения, обновления и удаления экземпляров OrderProduct
        через REST API. Основное внимание уделяется созданию нового заказа продукта, который включает в себя
        обработку корзины пользователя и отправку подтверждения заказа по электронной почте.

        Атрибуты:
            queryset (QuerySet): Набор данных для модели OrderProduct.
            serializer_class (Serializer): Сериализатор, используемый для валидации и
                преобразования данных OrderProduct.
        """
    queryset = OrderProduct.objects.all()
    serializer_class = OrderProductSerializer

    def create(self, request, *args, **kwargs):
        """
        Создает новый заказ на основе продуктов в корзине пользователя.

        Этот метод извлекает продукты из корзины текущего пользователя, создает новый экземпляр заказа и
        соответствующие экземпляры OrderProduct. Он также рассчитывает общую стоимость заказа, очищает корзину
        и отправляет подтверждение заказа по электронной почте.

        Параметры:
            request (Request): Объект запроса, содержащий данные о заказе и
                информацию о пользователе.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Возвращает:
            Response: Ответ с сообщением об успешном создании заказа и
            статусом HTTP 201 (Created).

        Примечание:
            Если в корзине нет продуктов, будет создан пустой заказ.
            Убедитесь, что корзина пользователя не пуста перед вызовом этого метода.
        """
        basket = request.user.basket
        basketproducts = basket.position.all()
        order = Order.objects.create(user=request.user,
                                     status='active',
                                     delivery_address=request.data.get("delivery_address", request.user.address))
        total_price = 0
        products_list = []
        for basketproduct in basketproducts:
            order_product = OrderProduct.objects.create(order=order, product=basketproduct.product, quantity=basketproduct.quantity)
            total_price += order_product.product.price * order_product.quantity
            products_list.append(f"{order_product.product.name} - {order_product.quantity} шт. по цене {order_product.product.price} руб.")

        order.total_price = total_price
        order.save()
        basket.position.all().delete()

        send_order_confirmation_email.delay(order.pk, products_list, total_price, request.user.email)

        data_for_suppliers = [
            {
                'product': product.name,
                'shop': product.shop.name,
                'email': product.shop.user.email
            }
            for product in order.product.all()
        ]
        send_order_confirmation_to_suppliers.delay(data_for_suppliers)


        return Response({'message': f'Заказ № {order.pk} успешно создан'}, status=status.HTTP_201_CREATED)


def trigger_error(request):
    division_by_zero = 1 / 0