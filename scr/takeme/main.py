from fastapi import FastAPI
from models.database import init_db
from api import game_router, chat_router, action_router, record_router

app = FastAPI(title="带我玩 API", version="1.0")

# 注册路由
app.include_router(game_router.router)
app.include_router(chat_router.router)
app.include_router(action_router.router)
app.include_router(record_router.router)

@app.on_event("startup")
def on_startup():
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)