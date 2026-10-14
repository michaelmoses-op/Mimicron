from fastapi import APIRouter

from app.api.v1 import api_keys, auth, internal, me, runs, scenarios, stream_tokens, telemetry, traffic

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(stream_tokens.router)
api_router.include_router(api_keys.router)
api_router.include_router(scenarios.router)
api_router.include_router(runs.router)
api_router.include_router(telemetry.router)
api_router.include_router(traffic.router)
api_router.include_router(internal.router)
