from celery import shared_task
from django.core.mail import send_mail

# from market.celery import app
import environ

env = environ.Env()
environ.Env.read_env()

@shared_task
def send_order_confirmation_email(order, products_list, total_price, to_email):

    subject = 'Подтверждение заказа'
    message = (
        f'Заказ №{order} создан успешно!\n\n'
        f'Список товаров:\n{", ".join(products_list)}\n\n'
        f'Общая стоимость: {total_price} руб.'
    )
    from_email = env("EMAIL_HOST")


    send_mail(subject, message, from_email, [to_email])


@shared_task
def send_order_confirmation_to_suppliers(data: list):
    for sup in data:
        subject = f"Уведомление о заказе: {sup.get("product")} был заказан"
        message = (
            f"Уважаемый(ая) {sup.get("shop")},\n\nМы получили заказ на {sup.get("product")}. Пожалуйста, подготовьте"
                   f" продукт к отправке.\n\nС уважением, [Название вашей компании]"
        )
        from_email = env("EMAIL_HOST")
        send_mail(subject, message, from_email, [sup.get("email")])
