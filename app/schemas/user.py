"""
schemas/user.py
---------------
Define los esquemas Pydantic para validar datos de entrada y salida
relacionados con usuarios. Separa lo que el cliente envía (input)
de lo que la API retorna (output).
"""

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    """Datos requeridos para registrar un nuevo usuario."""
    email: EmailStr       # Pydantic valida que sea un email válido
    username: str
    password: str         # Se recibe en texto plano, se hashea antes de guardar


class UserLogin(BaseModel):
    """Datos requeridos para iniciar sesión."""
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """
    Datos del usuario que retorna la API.
    Nunca incluye la contraseña ni el hash.
    """
    id: int
    email: str
    username: str
    is_active: bool
    role: str
    model_config = {"from_attributes": True}  # permite convertir modelos ORM a este schema


class Token(BaseModel):
    """Respuesta del endpoint de login."""
    access_token: str
    token_type: str = "bearer"