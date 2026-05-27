from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from schemas.chat_schema import SendMessageRequest
from services.chat_service import ChatService
import json

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/send")
def send_message(req: SendMessageRequest):
    service = ChatService()
    result = service.handle_message(req.game_uid, req.content, req.time_passed_min)

    # 如果返回了错误，直接返回字典 (FastAPI 会自动序列化为 JSON)
    if result.get("code") != 200:
        return result

    inner_data = result.get("data", {})
    segments = inner_data.get("segments", [])
    system_reply = inner_data.get("system_reply", "")
    new_status = inner_data.get("new_status")
    full_reply = inner_data.get("reply", "")

    def generate():
        # 逐段发送消息给前端
        for i, segment in enumerate(segments):
            event_data = json.dumps({"segment": segment, "seq": i + 1}, ensure_ascii=False)
            yield f"event: message\ndata: {event_data}\n\n"

        # 有系统裁定或状态变更时，发送 status 事件
        if new_status:
            status_data = json.dumps({"updates": new_status, "system_reply": system_reply}, ensure_ascii=False)
            yield f"event: status\ndata: {status_data}\n\n"

        # 发送完成 done 事件
        done_data = json.dumps({"reply": full_reply}, ensure_ascii=False)
        yield f"event: done\ndata: {done_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@router.get("/history")
def get_history(game_uid: str):
    service = ChatService()
    return service.get_history(game_uid)