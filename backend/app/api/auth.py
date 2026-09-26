from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.user import LoginRequest, LoginResponse, UserCreate, UserRead
from backend.app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Users & Authentication"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: DatabaseSession) -> LoginResponse:
    auth_service = AuthService(db)
    auth_service.seed_initial_users_if_empty()
    return auth_service.authenticate(data)


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(data: UserCreate, db: DatabaseSession) -> UserRead:
    return UserRead.model_validate(AuthService(db).register_user(data))


@router.get("/users", response_model=list[UserRead])
def list_users(db: DatabaseSession) -> list[UserRead]:
    auth_service = AuthService(db)
    auth_service.seed_initial_users_if_empty()
    return [UserRead.model_validate(u) for u in auth_service.list_users()]
