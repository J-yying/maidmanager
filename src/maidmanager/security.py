"""极简鉴权与账号隔离工具。"""

from typing import Dict, Optional

from fastapi import Header, HTTPException, status

# 允许多个账号用于数据隔离；可根据需要扩展。
ACCOUNTS: Dict[str, Dict[str, str]] = {
    "manager": {"password": "manager123", "role": "manager"},
    "manager1": {"password": "manager123", "role": "manager"},
    "investor": {"password": "investor123", "role": "investor"},
}


def _parse_token(token: str) -> Optional[str]:
    prefix = "fake-token-"
    if token.startswith(prefix):
        username = token[len(prefix) :]
        if username in ACCOUNTS:
            return username
    return None


def get_current_account(
    authorization: Optional[str] = Header(None),
) -> Dict[str, str]:
    """从 Authorization 头中提取账号信息，格式：Bearer fake-token-<username>。"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或无效的身份凭证",
        )
    token = authorization.split(" ", 1)[1].strip()
    username = _parse_token(token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的身份凭证",
        )
    account = ACCOUNTS[username]
    return {"username": username, "role": account["role"]}
