from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import insert, select
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
import os

from app.backend.db_depends import get_db
from app.models.user import User
from app.schemas import CreateUser


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = 'HS256'

router = APIRouter(prefix="/auth", tags=["auth"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def create_access_token(username: str, user_id: int, is_admin: bool, is_supplier: bool, is_customer: bool, expires_delta: timedelta):
    payload = {
        "sub": username,
        "id": user_id,
        "is_admin": is_admin,
        "is_supplier": is_supplier,
        "is_customer": is_customer,
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    # Преобразование datetime в timestamp (количество секунд с начала эпохи)
    payload["exp"] = int(payload["exp"].timestamp())
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def authenticate_user(db: AsyncSession,
                            username: str, password: str):
    user: User = await db.scalar(select(User).where(User.username == username))
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credantials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


@router.post("/token")
async def login(db: Annotated[AsyncSession, Depends(get_db)], 
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(db, form_data.username, form_data.password)
    token = await create_access_token(username=user.username,
                                      user_id=user.id,
                                      is_admin=user.is_admin,
                                      is_supplier=user.is_supplier,
                                      is_customer=user.is_customer,
                                      expires_delta=timedelta(minutes=20))
    return {
        "access_token": token,
        "token_type": "bearer"
    }


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        user_id: int | None = payload.get("id")
        is_admin: bool | None = payload.get("is_admin")
        is_supplier: bool | None = payload.get("is_supplier")
        is_customer: bool | None = payload.get("is_customer")
        expire: bool | None = payload.get("exp")

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user"
            )
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        if not isinstance(expire, int):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token format"
            )
        # Проверка срока действия токена
        current_time = datetime.now(timezone.utc).timestamp()
        if expire < current_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired!"
            )
        return {
            "username": username,
            "id": user_id,
            "is_admin": is_admin,
            "is_supplier": is_supplier,
            "is_customer": is_customer

        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired!"
        )
    except jwt.exceptions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )


@router.get("/read_current_user")
async def read_current_user(user: dict = Depends(get_current_user)):
    return {"User": user}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: Annotated[AsyncSession, Depends(get_db)], create_user: CreateUser):
    await db.execute(insert(User).values(
        first_name=create_user.first_name,
        last_name=create_user.last_name,
        email=create_user.email,
        username=create_user.username,
        hashed_password=bcrypt_context.hash(create_user.password)
    ))

    await db.commit()

    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "Successful"
    }
