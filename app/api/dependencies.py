"""
dependencies.py
---------------
Define dependencias reutilizables para los endpoints de FastAPI.
La más importante es get_current_user, que protege los endpoints
que requieren autenticación.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import User
from app.core.security import decode_token

# Le indica a FastAPI dónde está el endpoint de login para obtener el token.
# Esto habilita el botón "Authorize" en el Swagger /docs.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependencia que extrae y valida el token JWT del header Authorization.
    Si el token es válido, retorna el usuario autenticado.
    Si no, lanza un error 401.

    Uso en endpoints:
        @router.get("/me")
        async def me(current_user: User = Depends(get_current_user)):
            return current_user
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