"""Loopback-only browser fixture; never imported by the deployed API."""
import asyncio
from fastapi import Request
from fastapi.responses import JSONResponse
from app.main import app

faults: dict[str, dict] = {}


@app.post('/__test/cart-fault')
async def configure_fault(request: Request):
    """Set faults for one disposable session, isolating parallel browser tests."""
    body = await request.json()
    faults[body['token']] = body.get('fault', {})
    return {'ok': True}


@app.middleware('http')
async def cart_fault(request: Request, call_next):
    """Inject failures at FastAPI's boundary, including committed-write timeouts."""
    token = request.headers.get('authorization', '').removeprefix('Bearer ')
    fault = faults.get(token, {})
    path = request.url.path
    kind = 'identity' if path == '/api/v1/auth/me' else (
        'read' if path == '/api/v1/cart/' else 'write'
    )
    if path != '/api/v1/auth/me' and not path.startswith('/api/v1/cart/'):
        return await call_next(request)
    mode = fault.get(kind)
    if mode in ('timeout-after-write', 'fail-after-write'):
        mode = mode.removesuffix('-after-write') if fault.get('written') else None
    if mode == 'fail':
        return JSONResponse({'detail': 'fixture failure'}, status_code=503)
    if mode == 'timeout':
        await asyncio.sleep(20)
    if mode == 'delay':
        await asyncio.sleep(1)
    response = await call_next(request)
    if kind == 'write':
        fault['written'] = True
    if mode == 'timeout-after':
        await asyncio.sleep(20)
    return response
