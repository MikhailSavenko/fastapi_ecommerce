from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select

from app.backend.db_depends import get_db
from app.schemas import CreateProduct
from app.models.products import Product
from app.models.category import Category
from .auth import get_current_user

router = APIRouter(prefix="/products", tags=["products"])


@router.get('/')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).join(Category).where(Product.is_active == True, Product.stock > 0))
    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no products"
        )
    return products.all()


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], 
                         create_product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        category = await db.scalar(select(Category).where(Category.id == create_product.category))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no category found"
            )
        await db.execute(insert(Product).values(
            supplier_id=get_user.get("id"),
            name=create_product.name,
            slug=slugify(create_product.name),
            price=create_product.price,
            image_url=create_product.image_url,
            stock=create_product.stock,
            category_id=create_product.category,
            description=create_product.description,
            rating=0.0
        ))
        await db.commit()
        return {
            "status_code": status.HTTP_201_CREATED,
            "transaction": "Successful"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method"
        )


@router.get("/{category_slug}")
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no category"
        )
    subcategories = await db.scalars(select(Category).where(Category.parent_id == category.id))
    all_category = [category.id, *(sub.id for sub in subcategories.all())]
    products = await db.scalars(select(Product).where(Product.category_id.in_(all_category), Product.is_active == True, Product.stock > 0))
    return products.all()


@router.get("/detail/{product_slug}")
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug, Product.is_active == True, Product.stock > 0))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product"
        )
    return product


@router.put("/{product_slug}")
async def update_product(db: Annotated[AsyncSession, Depends(get_db)], 
                         product_slug: str, 
                         update_product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        product = await db.scalar(select(Product).where(Product.slug == product_slug))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no product"
            )
        if get_user.get("id") == product.supplier_id or get_user.get("is_admin"):
            category = await db.scalar(select(Category).where(Category.id == update_product.category))
            if category is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="There is no category"
                )
            product.name = update_product.name,
            product.slug = slugify(update_product.name)
            product.price = update_product.price
            product.image_url = update_product.image_url
            product.stock = update_product.stock
            product.category_id = update_product.category
            product.description = update_product.description

            await db.commit()

            return {
                "status_code": status.HTTP_200_OK,
                "transaction": "Product update is successful"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have not enough permission for this action"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method"
        )


@router.delete("/{product_slug}")
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], 
                         product_slug: str,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        product = await db.scalar(select(Product).where(Product.slug == product_slug))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no product"
            )
        if get_user.get("id") == product.supplier_id or get_user.get("is_admin"):
            product.is_active = False

            await db.commit()

            return {
                "status_code": status.HTTP_200_OK,
                "transaction": "Product delete is successful"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have not enough permission for this action"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method"
        )