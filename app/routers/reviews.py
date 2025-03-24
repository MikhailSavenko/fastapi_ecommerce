from fastapi import Depends, HTTPException, status, APIRouter
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, func, update

from app.backend.db_depends import get_db
from app.models.reviews import Reviews
from app.models.products import Product
from app.schemas import CreateReview
from .auth import get_current_user

router = APIRouter(prefix="/reviews", tags=["reviews"])


async def get_avg_rating(db: AsyncSession, product_id: int) -> float:
    result = await db.scalar(select(func.avg(Reviews.grade)).where(Reviews.product_id == product_id))
    return result or 0.0


@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_review(db: Annotated[AsyncSession, Depends(get_db)], 
                     get_user: Annotated[dict, Depends(get_current_user)],
                     create_review: CreateReview):
    if get_user.get("is_customer"):
        # Проверим сущуствование продукта
        product_exist = await db.scalar(select(Product).where(Product.id == create_review.product_id))
        if product_exist is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product does not exist"
            )
        # Добавим отзыв
        await db.execute(insert(Reviews).values(
            user_id=get_user.get("id"),
            product_id=create_review.product_id,
            comment=create_review.comment,
            grade=create_review.grade,
            comment_date=func.now()
        ))
        # Найдем среднее значение рейтинга по товару в отзывах
        mean_grade = await get_avg_rating(db=db, product_id=create_review.product_id)
        # Изменим рейтинг продукта
        await db.execute(update(Product).where(Product.id == create_review.product_id).values(rating=mean_grade))
        
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


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_id: int,
                        db: Annotated[AsyncSession, Depends(get_db)], 
                        get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin"):
        review = await db.scalar(select(Reviews).where(Reviews.id == review_id))
        if review is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review is not found"
            )
        if not review.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review already deleted"
            )
        review.is_active = False
        await db.commit()
        return {
            "status_code": status.HTTP_204_NO_CONTENT,
            "transaction": "Successful"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to use this method"
        )
    

@router.get("/")
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await db.scalars(select(Reviews).where(Reviews.is_active == True))
    return reviews.all()


@router.get("/product/{product_id}")
async def products_reviews(product_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    product = await db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product is not found"
        )
    reviews = await db.scalars(select(Reviews).where(Reviews.product_id == product_id))
    return reviews.all()