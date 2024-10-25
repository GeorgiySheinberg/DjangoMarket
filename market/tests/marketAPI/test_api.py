"""
На время тестирования необходимо отключать отправку писем в библиотеке djoser, иначе возникают проблемы с сериализацией.
"""
from random import randint

import pytest
import yaml

from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APIClient

from marketAPI.models import UserType, User, Shop, ExtraParameter, ProductCategory, Product


@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def create_user_types():
    for user_type in ('admin', 'customer', 'shop'):
            UserType.objects.update_or_create(type=user_type)


@pytest.fixture
def get_new_customer(client, create_user_types):

    client.post(path="/auth/users/",
                data={"email": "test_customer@oknhwe.com", "password": "12345asdf"},
                format='json')

    response = client.post(path="/auth/token/login/",
                           data={"email": "test_customer@oknhwe.com", "password": "12345asdf"},
                           format='json')

    return response.data.get("auth_token")


@pytest.fixture
def get_new_shop(client, create_user_types):

    client.post(path="/auth/users/",
                data= {"email": "test_shop@oknhwe.com", "password": "12345asdf"},
                format='json')

    response = client.post(path="/auth/token/login/",
                           data={"email": "test_shop@oknhwe.com", "password": "12345asdf"},
                           format='json')

    u = User.objects.get(email="test_shop@oknhwe.com")
    u.type_id = 3
    s = Shop.objects.create(name='Связной', url='testurl')
    u.shop_id = s.id
    u.save()
    return response.data.get("auth_token")

@pytest.fixture
def fill_products_to_db(get_new_shop):
    shop_id = 1
    yaml_file_path = r"tests/marketAPI/test_files/shop1.yaml"
    with open(yaml_file_path, 'r') as file:
        data = yaml.safe_load(file)
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


@pytest.mark.django_db
def test_registration(client, create_user_types):
    """
        Тестирование процесса регистрации пользователей в приложении.

        Цель:
        Проверить, что процесс регистрации работает корректно и обрабатывает различные сценарии,
        включая успешную регистрацию и ошибки валидации.

        Шаги теста:
    1. Создание нескольких типов пользователей (admin, user, shop) с помощью bulk_create.
        2. Попытка зарегистрировать нового пользователя с валидными данными (email и password).
           Ожидается, что сервер вернет статус 201 (Created).
        3. Попытка зарегистрировать пользователя с уже существующим email без указания пароля.
           Ожидается, что сервер вернет статус 400 (Bad Request) с соответствующими сообщениями об ошибках.
        4. Попытка зарегистрировать пользователя с валидным email, но слишком коротким паролем.
           Ожидается, что сервер вернет статус 400 с сообщением о том, что пароль слишком короткий.
        5. Попытка зарегистрировать пользователя с некорректным форматом email.
           Ожидается, что сервер вернет статус 400 с сообщением о том, что email недействителен.

        Ожидаемые результаты:
        - Успешная регистрация должна вернуть статус 201.
        - Все ошибки валидации должны возвращать статус 400 с соответствующими сообщениями.
        """

    response = client.post(
        path="/auth/users/",
        data={"email": "test_email1@oknhwe.com", "password": "12345asdf"},
        format='json')
    assert response.status_code == 201

    response = client.post(
        path="/auth/users/",
        data={"email": "test_email1@oknhwe.com"},
        format='json')
    assert response.json().get("email")[0] == 'user with this email already exists.'
    assert response.json().get("password")[0] == 'This field is required.'
    assert response.status_code == 400

    response = client.post(
        path="/auth/users/",
        data={"email": "test_email3@oknhwe.com", "password": "short"},
        format='json'
    )
    assert response.status_code == 400
    assert response.json().get("password")[0] == 'This password is too short. It must contain at least 8 characters.'

    response = client.post(
        path="/auth/users/",
        data={"email": "invalid_email_format", "password": "12345asdf"},
        format='json'
    )
    assert response.status_code == 400
    assert response.json().get("email")[0] == 'Enter a valid email address.'


@pytest.mark.django_db
def test_partner_update(client, get_new_shop, get_new_customer):
    """
        Тестирование функциональности обновления партнера через API.

        Этот тест проверяет несколько сценариев, связанных с обновлением данных
        партнера, используя файл YAML.

        1. **Успешное обновление**: - Открывается файл shop1.yaml и отправляется POST-запрос на эндпоинт "/update/" с заголовком авторизации и загруженным файлом.
           - Ожидается, что статус ответа будет 200 и содержимое JSON-ответа
             будет {'Status': 'OK'}.

        2. **Отсутствие файла**:
           - Отправляется POST-запрос на тот же эндпоинт без файла.
           - Ожидается, что ответ будет содержать статус False и сообщение об ошибке 'No file provided'.

        3. **Неверный формат файла**:
           - Открывается файл cat(not YAML file).jpg и отправляется POST-запрос с этим файлом.
           - Ожидается, что ответ будет содержать статус False и сообщение об ошибке 'Invalid YAML file'.

        4. **Попытка обновления с другим пользователем**:
           - Снова открывается файл shop1.yaml и отправляется POST-запрос с
             авторизацией другого пользователя (get_new_customer).
           - Ожидается, что ответ будет содержать статус False и сообщение об ошибке 'Shop only', что указывает на то, что только определенные
             пользователи могут выполнять это действие.

        Этот тест обеспечивает проверку различных аспектов обработки файлов и авторизации в API, что помогает гарантировать корректную работу
        функциональности обновления партнера.
        """
    path =  "tests/marketAPI/test_files"
    with open(f'{path}/shop1.yaml' , 'rb') as fp:
        uploaded_file = SimpleUploadedFile("shop1.yaml", fp.read(), content_type='application/x-yaml')

    response = client.post(
            path="/update/",
            headers={"Authorization": f'Token {get_new_shop}'},
            data={'file': uploaded_file},
            format='multipart'
        )

    assert response.status_code == 200
    assert response.json() == {'Status': 'OK'}

    response = client.post(
        path="/update/",
        headers={"Authorization": f'Token {get_new_shop}'},
        format='multipart'
    )
    assert response.json().get("Status") == False and response.json().get("Error") == 'No file provided'

    with open(f"{path}/cat(not YAML file).jpg" , 'rb') as fp:
        uploaded_file = SimpleUploadedFile("cat(not YAML file).jpg", fp.read(), content_type='application/x-yaml')

    response = client.post(
        path="/update/",
        headers={"Authorization": f'Token {get_new_shop}'},
        data={'file': uploaded_file},
        format='multipart'
    )
    assert response.json().get("Status") == False and response.json().get("Error") == 'Invalid YAML file'

    with open(f"{path}/shop1.yaml" , 'rb') as fp:
        uploaded_file = SimpleUploadedFile("marketAPI/shop1.yaml", fp.read(), content_type='application/x-yaml')

    response = client.post(
            path="/update/",
            headers={"Authorization": f'Token {get_new_customer}'},
            data={'file': uploaded_file},
            format='multipart'
        )

    assert  response.json().get("Status") == False and response.json().get("Error") == 'Shop only'


@pytest.mark.django_db
def test_product_view(get_new_shop, fill_products_to_db, client):
    """
    Тест для проверки корректноти отображения списка продуктов через API.

    Этот тест выполняет следующие проверки:
    1. Отправляет GET-запрос на эндпоинт /products/ и проверяет, что ответ имеет статус 200.
    2. Проверяет, что каждый продукт в ответе содержит необходимые ключи:
       'id', 'name', 'model', 'product_quantity', 'price'.
    3. Для каждого продукта отправляет GET-запрос на эндпоинт /product/{id}/ и проверяет,
       что ответ также имеет статус 200.
    4. Убедитесь, что ответ для каждого продукта содержит ключ 'extra_parameters'.

    Параметры:
    - get_new_shop: фикстура для создания нового магазина.
    - fill_products_to_db: фикстура для заполнения базы данных продуктами.
    - client: тестовый клиент Django для выполнения запросов к API.

    Ожидаемое поведение:
    - Все запросы должны возвращать статус 200.
    - Все продукты должны содержать необходимые ключи.
    - Ответы для каждого продукта должны содержать ключ 'extra_parameters'.
    """
    response = client.get(path="/products/", format='json')
    assert response.status_code == 200

    for item in response.json():
        assert all(key in item for key in ['id', 'name', 'model', 'product_quantity', 'price'])
        response = client.get(path=f'/product/{item.get('id')}/', format="json")
        assert response.status_code == 200
        assert 'extra_parameters' in response.json()


@pytest.mark.django_db
def test_basket(client, get_new_shop, get_new_customer, fill_products_to_db):
    """
    Тестирование функциональности корзины для добавления и получения продуктов.

    Этот тест выполняет следующие действия:
    1. Получает список достпных продуктов из API.
    2. Добавляет случайное количество (от 1 до 3) каждого продукта в корзину пользователя.
    3. Проверяет, что ответ на запрос добавления продукта в корзину содержит необходимые поля.
    4. Получает список продуктов в корзине пользователя.
    5. Проверяет, что ответ на запрос получения корзины содержит необходимые поля для каждого продукта,
       а также поля для информации о корзине.

    Параметры:
        client: Фикстура для тестирования API, предоставляющая клиент для выполнения запросов.
        get_new_shop: Фикстура для создания нового магазина (используется для заполнения данных в тесте).
        get_new_customer: Фикстура для создания нового клиента (используется для аутентификации).
        fill_products_to_db: Фикстура для заполнения базы данных продуктами перед тестом.

    Ожидаемые результаты:
        - Все запросы к API возвращают корректные ответы с необходимыми полями.
        - Продукты успешно добавляются в корзину и отображаются при получении списка продуктов в корзине.
    """
    response = client.get(path="/products/", format='json')
    products_ids = [item.get("id") for item in response.json()]
    for products_id in products_ids:
        response = (client.post(
            path='/basket/',
            headers={"Authorization": f'Token {get_new_customer}'},
            data={
                "product": products_id,
                "quantity": randint(1, 3)
            },
            format='json',
                               ))
        assert all(key in response.json() for key in ['id', 'basket', 'product', 'quantity'])

    response = client.get(
        path='/basket/',
        headers={"Authorization": f'Token {get_new_customer}'},
        format='json')

    for item in response.json():
        assert all(key in item for key in ['id', 'basket', 'product', 'total_price'])
        assert all(key in item.get("product") for key in ['id', 'name', 'price'])