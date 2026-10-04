from fastapi import APIRouter

from app.api.v1 import api_keys, auth, internal, me

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(api_keys.router)
api_router.include_router(internal.router)
