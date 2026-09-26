import hashlib
import hmac
import os
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.repositories.user import UserRepository
from backend.app.schemas.user import LoginRequest, LoginResponse, UserCreate, UserRead, UserRole

security = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str | None = None) -> str:
    if not salt:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${hashed}"


def verify_password(password: str, hashed_password: str) -> bool:
    if "$" not in hashed_password:
        return False
    salt, hashed = hashed_password.split("$", 1)
    return hmac.compare_digest(hash_password(password, salt), hashed_password)


class AuthService:
    """Authentication, password management, and user operations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = UserRepository(db)

    def register_user(self, data: UserCreate) -> User:
        if self.repository.get_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this username already exists.",
            )
        if self.repository.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        user = User(
            username=data.username,
            full_name=data.full_name,
            email=data.email,
            phone=data.phone,
            hashed_password=hash_password(data.password),
            role=data.role.value,
            branch=data.branch,
            is_active=True,
        )
        self.repository.create(user)
        return self.repository.save(user)

    def authenticate(self, data: LoginRequest) -> LoginResponse:
        user = self.repository.get_by_username(data.username)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated.",
            )

        # Generate simple token containing user ID and username
        token = f"token_{user.id}_{user.username}"
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=UserRead.model_validate(user),
        )

    def list_users(self) -> list[User]:
        return self.repository.list()

    def seed_initial_users_if_empty(self) -> None:
        """Seeds default Admin General and Branch Admins if the database is fresh."""
        if not self.repository.list():
            self.register_user(
                UserCreate(
                    username="admin_general",
                    full_name="Directora General",
                    email="administracion@garboysalero.pe",
                    phone="+51 987 654 321",
                    password="adminpassword123",
                    role=UserRole.ADMIN_GENERAL,
                    branch="Todas",
                )
            )
            self.register_user(
                UserCreate(
                    username="admin_olivos",
                    full_name="Administrador Los Olivos",
                    email="olivos@garboysalero.pe",
                    phone="+51 987 654 322",
                    password="olivospassword123",
                    role=UserRole.ADMIN_SEDE,
                    branch="Los Olivos",
                )
            )
            self.register_user(
                UserCreate(
                    username="admin_comas",
                    full_name="Administrador Comas",
                    email="comas@garboysalero.pe",
                    phone="+51 987 654 323",
                    password="comaspassword123",
                    role=UserRole.ADMIN_SEDE,
                    branch="Comas",
                )
            )
