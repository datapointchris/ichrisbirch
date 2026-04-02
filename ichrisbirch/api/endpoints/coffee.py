import structlog
from fastapi import APIRouter
from fastapi import Query
from fastapi import Response
from fastapi import status
from sqlalchemy import select

from ichrisbirch import models
from ichrisbirch import schemas
from ichrisbirch.api.endpoints.auth import DbSession
from ichrisbirch.api.exceptions import NotFoundException

logger = structlog.get_logger()

# ── Coffee Shops ──────────────────────────────────────────────────────────────
shops_router = APIRouter()


@shops_router.get('/', response_model=list[schemas.CoffeeShop], status_code=status.HTTP_200_OK)
async def read_many_shops(session: DbSession, city: str | None = Query(None)):
    query = select(models.CoffeeShop).order_by(models.CoffeeShop.name.asc())
    if city:
        query = query.filter(models.CoffeeShop.city.ilike(f'%{city}%'))
    return list(session.scalars(query).all())


@shops_router.post('/', response_model=schemas.CoffeeShop, status_code=status.HTTP_201_CREATED)
async def create_shop(shop: schemas.CoffeeShopCreate, session: DbSession):
    obj = models.CoffeeShop(**shop.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    logger.info('coffee_shop_created', name=obj.name)
    return obj


@shops_router.get('/{id}/', response_model=schemas.CoffeeShop, status_code=status.HTTP_200_OK)
async def read_one_shop(id: int, session: DbSession):
    if shop := session.get(models.CoffeeShop, id):
        return shop
    raise NotFoundException('coffee shop', id, logger)


@shops_router.patch('/{id}/', response_model=schemas.CoffeeShop, status_code=status.HTTP_200_OK)
async def update_shop(id: int, shop_update: schemas.CoffeeShopUpdate, session: DbSession):
    update_data = shop_update.model_dump(exclude_unset=True)
    logger.debug('coffee_shop_update', shop_id=id, update_data=update_data)
    if shop := session.get(models.CoffeeShop, id):
        for attr, value in update_data.items():
            setattr(shop, attr, value)
        session.commit()
        session.refresh(shop)
        return shop
    raise NotFoundException('coffee shop', id, logger)


@shops_router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_shop(id: int, session: DbSession):
    if shop := session.get(models.CoffeeShop, id):
        session.delete(shop)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise NotFoundException('coffee shop', id, logger)


# ── Coffee Beans ──────────────────────────────────────────────────────────────
beans_router = APIRouter()


@beans_router.get('/', response_model=list[schemas.CoffeeBean], status_code=status.HTTP_200_OK)
async def read_many_beans(
    session: DbSession,
    roast_level: str | None = Query(None),
    brew_method: str | None = Query(None),
    coffee_shop_id: int | None = Query(None),
):
    query = select(models.CoffeeBean).order_by(models.CoffeeBean.name.asc())
    if roast_level:
        query = query.filter(models.CoffeeBean.roast_level == roast_level)
    if brew_method:
        query = query.filter(models.CoffeeBean.brew_method == brew_method)
    if coffee_shop_id is not None:
        query = query.filter(models.CoffeeBean.coffee_shop_id == coffee_shop_id)
    return list(session.scalars(query).all())


@beans_router.post('/', response_model=schemas.CoffeeBean, status_code=status.HTTP_201_CREATED)
async def create_bean(bean: schemas.CoffeeBeanCreate, session: DbSession):
    obj = models.CoffeeBean(**bean.model_dump())
    session.add(obj)
    session.commit()
    session.refresh(obj)
    logger.info('coffee_bean_created', name=obj.name, roaster=obj.roaster)
    return obj


@beans_router.get('/{id}/', response_model=schemas.CoffeeBean, status_code=status.HTTP_200_OK)
async def read_one_bean(id: int, session: DbSession):
    if bean := session.get(models.CoffeeBean, id):
        return bean
    raise NotFoundException('coffee bean', id, logger)


@beans_router.patch('/{id}/', response_model=schemas.CoffeeBean, status_code=status.HTTP_200_OK)
async def update_bean(id: int, bean_update: schemas.CoffeeBeanUpdate, session: DbSession):
    update_data = bean_update.model_dump(exclude_unset=True)
    logger.debug('coffee_bean_update', bean_id=id, update_data=update_data)
    if bean := session.get(models.CoffeeBean, id):
        for attr, value in update_data.items():
            setattr(bean, attr, value)
        session.commit()
        session.refresh(bean)
        return bean
    raise NotFoundException('coffee bean', id, logger)


@beans_router.delete('/{id}/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_bean(id: int, session: DbSession):
    if bean := session.get(models.CoffeeBean, id):
        session.delete(bean)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise NotFoundException('coffee bean', id, logger)
