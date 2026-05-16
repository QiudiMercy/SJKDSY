from fastapi.responses import JSONResponse

def success(data=None, msg="success"):
    return JSONResponse(content={
        "code": 200,
        "msg": msg,
        "data": data
    })

def error(code=400, msg="error", data=None):
    return JSONResponse(status_code=code, content={
        "code": code,
        "msg": msg,
        "data": data
    })