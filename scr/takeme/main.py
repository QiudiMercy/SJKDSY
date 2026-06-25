from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from models.database import init_db
from api import game_router, chat_router, action_router, record_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="带我玩 API", version="1.0", lifespan=lifespan)

# 注册 API 路由
app.include_router(game_router.router)
app.include_router(chat_router.router)
app.include_router(action_router.router)
app.include_router(record_router.router)

# 静态文件 — 挂载在 /static 子路径，与 /api 完全隔离
_STATIC_DIR = Path(__file__).parent.parent.parent  # main.py → takeme → scr → 项目根
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


# favicon — 浏览器自动请求 /favicon.ico，返回 SVG 亦可
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(str(_STATIC_DIR / "favicon.svg"), media_type="image/svg+xml")


# 首页
@app.get("/")
async def serve_index():
    return FileResponse(str(_STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("\nGame Backend Service Started!\nhttp://127.0.0.1:8000\n")
    # 保持 0.0.0.0 方便局域网访问
    uvicorn.run(app, host="0.0.0.0", port=8000)