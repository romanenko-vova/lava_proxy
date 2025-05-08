"""
Вспомогательные функции для обработки запросов.
"""

import json
import re
from fastapi import Request, HTTPException, status


async def parse_request_body(request: Request):
    """Парсит тело запроса и возвращает JSON-объект."""
    body = await request.body()
    print(f"Raw body: {body}")

    if not body:
        return {}

    try:
        body_str = body.decode("utf-8")
        if body_str:
            payload = json.loads(body_str)
            print(f"JSON body: {payload}")
            return payload
        return {}
    except Exception as e:
        print(f"Error parsing request body as JSON: {e}")
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"Cannot decode JSON: {e}"
        )


def build_salebot_params(
    utm_message: str,
    utm_clientid: str,
    contract_id: str,
    is_recurring: bool = False,
    days_add: int = None,
) -> dict:
    """Создает параметры для запроса к Salebot."""
    params = {
        "message": "Продление ГАМАРДЖОБА_ГЕНАЦВАЛЕ7447213141232"
        if is_recurring
        else utm_message + " ГАМАРДЖОБА_ГЕНАЦВАЛЕ1321312421",
        "client_id": utm_clientid,
        "contract_id": contract_id,
    }

    # Добавляем days_add, если указан
    if days_add is not None:
        params["days_add"] = str(days_add)

    return params


def get_subscription_days(message: str) -> int:
    """Определяет количество дней подписки по тексту сообщения.

    Примеры:
    - "Подписка 1 месяц" -> 30 дней
    - "Подписка 3 месяца" -> 90 дней
    - "Подписка 6 месяцев" -> 180 дней
    - "Подписка 12 месяцев" -> 365 дней
    """
    # Словарь соответствия месяцев и дней
    months_to_days = {
        1: 30,  # 1 месяц -> 30 дней
        3: 90,  # 3 месяца -> 90 дней
        6: 180,  # 6 месяцев -> 180 дней
        12: 365,  # 12 месяцев -> 365 дней
    }

    # Ищем число месяцев в строке
    match = re.search(r"Подписка\s+(\d+)\s+месяц", message, re.IGNORECASE)
    if match:
        months = int(match.group(1))
        # Возвращаем соответствующее количество дней или 30 по умолчанию
        return months_to_days.get(months, 30)

    # Если не удалось определить, возвращаем 30 дней по умолчанию
    return 30
