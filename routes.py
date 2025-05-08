"""
Модуль содержит маршруты FastAPI.
"""

import httpx
from fastapi import APIRouter, Request, HTTPException, status
from config import SALEBOT_API_TIMEOUT, CHATTER_CALLBACK_URL
from database import store_utm_metrics, get_utm_metrics, update_utm_metrics_timestamp
from helpers import parse_request_body, build_salebot_params, get_subscription_days

router = APIRouter()


@router.post("/payment", status_code=status.HTTP_200_OK)
async def new_lava_hook(request: Request):
    """New endpoint that accepts payment data from Lava."""
    print("New payment received")
    
    # Отладочная информация
    print(f"Request: {request}")
    print(f"Headers: {request.headers}")
    
    # Парсим тело запроса
    payload = await parse_request_body(request)
    
    # Получаем clientUtm из payload
    client_utm = payload.get("clientUtm", {})
    if not client_utm:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "clientUtm is required")
    
    # Сохраняем UTM-метки для этого контракта
    contract_id = payload.get("contractId")
    if contract_id:
        await store_utm_metrics(contract_id, client_utm)
    
    # Извлекаем нужные значения из client_utm
    utm_message = client_utm.get("utm_content", "")
    utm_clientid = client_utm.get("utm_source")
    
    if not utm_clientid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "clientUtm.utm_source is required")
    
    # Получаем contractId из payload
    contract_id = payload.get("contractId", "")
    
    # Подготовка параметров для запроса
    params = build_salebot_params(
        utm_message=utm_message, 
        utm_clientid=utm_clientid, 
        contract_id=contract_id,
        is_recurring=False,
        days_add=None
    )
    
    print(f"Forwarding to Chatter with params: {params}")
    
    # Отправка запроса на указанный URL
    async with httpx.AsyncClient(timeout=SALEBOT_API_TIMEOUT) as client:
        try:
            resp = await client.get(CHATTER_CALLBACK_URL, params=params)
        except httpx.RequestError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Error calling Chatter API: {exc}") from exc

    if resp.status_code >= 400:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Chatter API returned {resp.status_code}: {resp.text}")

    return {"status": "forwarded", "chatter_status": resp.status_code}


@router.post("/regular_pay", status_code=status.HTTP_200_OK)
async def regular_pay(request: Request):
    """New endpoint that accepts recurring payment data from Lava."""
    print("New recurring payment received")
    
    # Отладочная информация
    print(f"Request: {request}")
    print(f"Headers: {request.headers}")
    
    # Парсим тело запроса
    payload = await parse_request_body(request)
    
    # Получаем parentContractId
    parent_contract_id = payload.get("parentContractId")
    if not parent_contract_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "parentContractId is required")
    
    # Получаем UTM-метки из базы данных по parentContractId
    utm_data = await get_utm_metrics(parent_contract_id)
    if not utm_data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"No UTM metrics found for parent contract {parent_contract_id}")
    
    # Обновляем timestamp в базе данных для родительского контракта
    updated = await update_utm_metrics_timestamp(parent_contract_id)
    if not updated:
        print(f"Warning: Failed to update timestamp for parent contract {parent_contract_id}")
    
    # Извлекаем нужные значения из utm_data
    utm_message = utm_data.get("utm_content", "")
    utm_clientid = utm_data.get("utm_source")
    
    if not utm_clientid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No utm_source found in stored UTM metrics")
    
    # Получаем contractId из payload
    contract_id = payload.get("contractId", "")
    
    # Определяем количество дней на основе первоначального сообщения
    days_add = get_subscription_days(utm_message)
    
    # Подготовка параметров для запроса с пометкой, что это регулярный платеж и с days_add
    params = build_salebot_params(
        utm_message=utm_message, 
        utm_clientid=utm_clientid, 
        contract_id=contract_id,
        is_recurring=True,
        days_add=days_add
    )
    
    print(f"Forwarding to Chatter with params: {params}")
    
    # Отправка запроса на указанный URL
    async with httpx.AsyncClient(timeout=SALEBOT_API_TIMEOUT) as client:
        try:
            resp = await client.get(CHATTER_CALLBACK_URL, params=params)
        except httpx.RequestError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Error calling Chatter API: {exc}") from exc

    if resp.status_code >= 400:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Chatter API returned {resp.status_code}: {resp.text}")

    return {"status": "forwarded", "chatter_status": resp.status_code} 