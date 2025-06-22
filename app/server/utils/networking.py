from fastapi import Request

async def get_source_ip(request: Request):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        source_ip = x_forwarded_for.split(",")[0]
    else:
        source_ip = request.client.host
    return source_ip