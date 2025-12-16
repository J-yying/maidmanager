from fastapi import APIRouter, HTTPException, status

from .. import schemas

router = APIRouter(prefix="/api", tags=["auth"])


ACCOUNTS = {
    "manager": {"password": "manager123", "role": "manager"},
    "investor": {"password": "investor123", "role": "investor"},
}


@router.post(
    "/login",
    response_model=schemas.LoginResponse,
    summary="简易登录（固定账号密码）",
)
def login(payload: schemas.LoginRequest) -> schemas.LoginResponse:
    """固定账号密码的简易登录。

    当前不返回真实 JWT，仅返回一个假 token，供前端区分角色使用。
    """
    account = ACCOUNTS.get(payload.username)
    if not account or account["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    token = f"fake-token-{payload.username}"
    return schemas.LoginResponse(
        username=payload.username,
        role=account["role"],
        token=token,
    )

