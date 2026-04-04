# api/v1/chat/__init__.py
# Simplified to a single universal router.
from api.v1.chat.router import router

__all__ = ["router"]