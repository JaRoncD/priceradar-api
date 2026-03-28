"""
dependencies.py
---------------
Define dependencias reutilizables para los endpoints de FastAPI.

Dependencias disponibles:
    - get_current_user: valida el JWT y retorna el usuario autenticado
    - get_admin_user: igual que get_current_user pero exige rol 'admin'
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import User
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Valida el token JWT y retorna el usuario autenticado.
    Lanza 401 si el token es inválido o el usuario no existe.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if not payload:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Extiende get_current_user verificando que el usuario tenga rol 'admin'.
    Lanza 403 si el usuario no tiene permisos suficientes.

    Uso en endpoints:
        @router.post("/products")
        async def create(current_user: User = Depends(get_admin_user)):
            ...
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para realizar esta acción"
        )
    return current_user