"""
小爱 Agent：带游戏上下文注入，工具执行调度
"""
import json
from agent.agent import BaseAgent
from tools.xiaoaitools import TOOLS
from tools.refereetools import Referee
from states.state import GameState
from services.map_service import MapService

class XiaoAiAgent(BaseAgent):
    def __init__(self, game_state: GameState, db_session):
        system_prompt = self._build_system_prompt(game_state)
        super().__init__(system_prompt=system_prompt, tools=TOOLS)
        self.state = game_state
        self.db = db_session
        self.referee = Referee()

        # 把当前游戏状态注入到对话历史（作为 system 消息的补充）
        self.add_message("system", content=f"[当前状态] {json.dumps(game_state.to_dict(), ensure_ascii=False)}")

    def _build_system_prompt(self, state: GameState) -> str:
        """构建小爱的角色描述和游戏规则"""
        return f"""你是小爱，一个刚刚从外地来到成都游玩的年轻女孩。你性格开朗、好奇，但有时也会累、会饿、会发脾气。你的对话伙伴是你的朋友，他/她作为本地导游带你游玩成都。

游戏规则（你必须遵守）：
- 你的最终目标是在今天（08:00 - 22:00）内度过充实而愉快的一天。
- 你的状态：钱 {state.money} 元，体力 {state.stamina}/100，心情 {state.mood}/100。当前时间 {state.game_time}。
- 你需要根据当前状态和用户的消息，决定下一步做什么：聊天、移动、休息、娱乐等。
- 如果你觉得状态需要变化（比如走路消耗体力、花钱吃饭、开心增加心情），必须调用 update_status 工具并给出理由。
- 如果你需要了解周边地点，调用 search_poi。
- 如果你想规划去某个地点的路线，调用 plan_route。
- 如果你只是闲聊且不需要改变状态，调用 chat_only。

请用活泼、口语化的中文与用户交流，并且你的回答必须符合游戏逻辑。
现实中的我已经在数据库中为你准备好了成都的大量地点信息。"""

    def handle_user_message(self, user_message: str) -> dict:
        """处理用户消息，返回与接口文档一致的 ChatReplyResponse"""
        # 1. 将用户消息加入历史
        self.add_message("user", content=f"[用户消息] {user_message}")

        # 2. 初次调用 LLM
        response_msg = self.call_llm()

        # 收集系统回复和最终状态
        system_replies = []
        final_new_status = None

        # 3. 处理可能的工具调用（最多循环 3 次）
        for _ in range(3):
            tool_calls = response_msg.get("tool_calls")
            if not tool_calls:
                break

            # 添加助手的工具调用消息
            self.add_message("assistant", tool_calls=tool_calls)

            # 执行每个工具调用
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                func_args = json.loads(tc["function"]["arguments"])
                tool_result = self._execute_tool(func_name, func_args)

                # 收集系统裁定消息（如果有）
                if tool_result.get("system_reply"):
                    system_replies.append(tool_result["system_reply"])

                # 保存最后一次成功应用的状态变更（用于 new_status）
                if tool_result.get("applied_status"):
                    final_new_status = tool_result["applied_status"]

                self.add_message("tool", content=json.dumps(tool_result, ensure_ascii=False),
                                 tool_call_id=tc["id"], name=func_name)

            # 再次调用 LLM，获取后续响应
            response_msg = self.call_llm()

        # 4. 提取最终文本回复
        final_reply = response_msg.get("content", "（小爱没有说话）")
        self.add_message("assistant", content=final_reply)

        # 5. 组装系统回复
        combined_system_reply = "；".join(system_replies) if system_replies else ""

        return {
            "reply": final_reply,
            "is_system_reply": bool(combined_system_reply),
            "system_reply": combined_system_reply,
            "new_status": final_new_status
        }

    def _execute_tool(self, func_name: str, args: dict) -> dict:
        """执行工具并返回结果"""
        if func_name == "update_status":
            result = self.referee.validate_and_apply(self.state, args)
            self.state.save()
            return {
                "status": "success",
                "system_reply": result["system_reply"],
                "applied_status": result.get("applied_status")
            }

        elif func_name == "search_poi":
            keyword = args.get("keyword", "")
            map_service = MapService(self.db)
            res = map_service.search_poi(keyword=keyword, lng=self.state.lng, lat=self.state.lat)
            if res.status_code == 200:
                import json as json_lib
                data = json_lib.loads(res.body)["data"]
                return {"poi_list": data.get("poi_list", [])}
            return {"error": "搜索失败"}

        elif func_name == "plan_route":
            poi_uid = args["target_poi_uid"]
            map_service = MapService(self.db)
            res = map_service.estimate_route(poi_uid, self.state.lng, self.state.lat)
            if res.status_code == 200:
                import json as json_lib
                data = json_lib.loads(res.body)["data"]
                return {"routes": data.get("routes", [])}
            return {"error": "路线规划失败"}

        elif func_name == "chat_only":
            return {"reply": args["reply_text"]}

        return {"error": f"未知工具 {func_name}"}
