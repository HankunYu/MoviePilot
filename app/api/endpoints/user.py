from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.core.security import get_password_hash
from app.db import get_db
from app.db.models.user import User
from app.db.userauth import get_current_active_superuser, get_current_active_user

router = APIRouter()


@router.get("/", summary="所有用户", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    查询用户列表
    """
    users = current_user.list(db)
    return users


@router.post("/", summary="新增用户", response_model=schemas.Response)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    新增用户
    """
    user = current_user.get_by_name(db, name=user_in.name)
    if user:
        return schemas.Response(success=False, message="用户已存在")
    user_info = user_in.dict()
    if user_info.get("password"):
        user_info["hashed_password"] = get_password_hash(user_info["password"])
        user_info.pop("password")
    user = User(**user_info)
    user = user.create(db)
    return schemas.Response(success=True)


@router.put("/", summary="更新用户", response_model=schemas.Response)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
    _: User = Depends(get_current_active_superuser),
) -> Any:
    """
    更新用户
    """
    user_info = user_in.dict()
    if user_info.get("password"):
        user_info["hashed_password"] = get_password_hash(user_info["password"])
        user_info.pop("password")
    user = User.get_by_name(db, name=user_info["name"])
    if not user:
        return schemas.Response(success=False, message="用户不存在")
    user.update(db, user_info)
    return schemas.Response(success=True)


@router.delete("/{user_name}", summary="删除用户", response_model=schemas.Response)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_name: str,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    删除用户
    """
    user = current_user.get_by_name(db, name=user_name)
    if not user:
        return schemas.Response(success=False, message="用户不存在")
    user.delete_by_name(db, user_name)
    return schemas.Response(success=True)


@router.get("/current", summary="当前登录用户信息", response_model=schemas.User)
def read_current_user(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    当前登录用户信息
    """
    return current_user


@router.get("/{user_id}", summary="用户详情", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    查询用户详情
    """
    user = current_user.get(db, rid=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )
    if user == current_user:
        return user
    if not user.is_superuser:
        raise HTTPException(
            status_code=400,
            detail="用户权限不足"
        )
    return user
