import time
#import metadata for API
from app.server.document.api_meta_data import TAGS_META_DATA
#for error handling
#for logging
from app.server.logger.custom_logger import logger
#import routes
from app.server.endpoint.authenticate import router as authenticate
from app.server.endpoint.background_tasks import router as celery_router

#date related operations
from app.server.utils import date_utils
#implement fastAPI
from fastapi import FastAPI,Request
#exception to validate error
from fastapi.exceptions import RequestValidationError
#before request and after response
'''
CORSMiddleware is used to enable Cross-Origin Resource Sharing (CORS) for your FastAPI application. 
CORS is a security feature implemented by web browsers that prevents web pages from making requests to a different domain 
than the one that served the original page. This middleware adds the necessary headers to allow cross-origin requests to 
be made to your FastAPI application from different domains.
'''
from fastapi.middleware.cors import CORSMiddleware
'''
GZipMiddleware is used to enable gzip compression of HTTP responses sent from your FastAPI application. 
Gzip compression can significantly reduce the size of response data, resulting in faster transfer times and reduced bandwidth usage. 
This middleware automatically compresses response data if the requesting client supports gzip compression.
'''
from fastapi.middleware.gzip import GZipMiddleware

from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException
app=FastAPI(openapi_tags=TAGS_META_DATA , default_response_class=ORJSONResponse)

# add routes
app.include_router(authenticate, tags=['Authenticate'], prefix='/api/auth')
app.include_router(celery_router,tags=['Video to MP3'], prefix="/api/video")

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    route = request.url.path
    logger.debug(f'Request Processing Time Taken for {route}: {process_time} seconds')
    return response

#log when application start
@app.on_event('startup')
async def startup_event():
    logger.debug(f'Application Started: {str(date_utils.get_current_date_time())}')

#log when application shutdown
@app.on_event('shutdown')
def shutdown_event():
    logger.debug(f'App shutdown: {str(date_utils.get_current_date_time())}')