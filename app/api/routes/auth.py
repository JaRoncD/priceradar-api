"""
routes/auth.py
--------------
Endpoints de autenticación: registro y login.
No requieren token JWT porque son el punto de entrada a la app.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserRegister, UserLogin, UserOut, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Registra un nuevo usuario en la base de datos.
    Verifica que el email no esté en uso antes de crear el usuario.
    La contraseña se hashea con bcrypt antes de guardarla.
    """
    # Verificar si el email ya existe
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Autentica un usuario y retorna un token JWT.
    El token debe enviarse en el header Authorization: Bearer <token>
    en todos los endpoints protegidos.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    """
    Retorna los datos del usuario actualmente autenticado.
    Se usa para recuperar el perfil del usuario al cargar la app
    cuando ya existe un token guardado en el navegador.
    """
    return current_user