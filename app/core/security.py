"""
security.py
-----------
Maneja el hashing de contraseñas y la generación/verificación de tokens JWT.
Se importa en los endpoints de autenticación y en las dependencias.
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Contexto de encriptación usando bcrypt.
# bcrypt es el algoritmo recomendado para hashear contraseñas
# porque es lento por diseño, lo que dificulta ataques de fuerza bruta.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Convierte una contraseña en texto plano a su versión hasheada.
    Este hash es el que se guarda en la base de datos, nunca la contraseña original.

    Ejemplo:
        hash_password("mi_clave") → "$2b$12$..."
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Compara una contraseña en texto plano contra su hash almacenado.
    Retorna True si coinciden, False si no.

    Ejemplo:
        verify_password("mi_clave", "$2b$12$...") → True
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """
    Genera un token JWT firmado con la SECRET_KEY.
    El token expira según ACCESS_TOKEN_EXPIRE_MINUTES definido en .env.

    Args:
        data: diccionario con la info a codificar, normalmente {"sub": user_id}

    Ejemplo:
        create_access_token({"sub": "42"}) → "eyJhbGci..."
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """
    Decodifica y valida un token JWT.
    Retorna el payload si el token es válido, None si está expirado o es inválido.

    Ejemplo:
        decode_token("eyJhbGci...") → {"sub": "42", "exp": ...}
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None