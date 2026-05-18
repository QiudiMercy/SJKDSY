"""
系统裁定器：检查 LLM 请求的状态修改是否合法，并生成系统消息
"""
from states.state import GameState

class Referee:
    @staticmethod
    def validate_and_apply(state: GameState, updates: dict) -> dict:
        """
        updates 是 LLM 请求的更新，例如：
        {
            "money_delta": -35,
            "stamina_delta": -5,
            "mood_delta": 10,
            "time_advance_min": 25,
            "reason": "打车前往太古里"
        }
        返回系统裁定结果和最终应用后的状态快照
        """
        logs = []
        applied = {}

        # 金钱变动
        if "money_delta" in updates and updates["money_delta"] != 0:
            delta = int(updates["money_delta"])
            if delta < 0 and state.money + delta < 0:
                logs.append(f"余额不足以支付（需 {abs(delta)} 元，当前 {state.money} 元），操作被阻止")
            else:
                state.update_money(delta)
                logs.append(f"余额 {'+' if delta>0 else ''}{delta} 元")
                applied["money"] = state.money

        # 体力变动
        if "stamina_delta" in updates and updates["stamina_delta"] != 0:
            delta = int(updates["stamina_delta"])
            if delta < 0 and state.stamina + delta < 0:
                logs.append(f"体力不足（需 {abs(delta)}，当前 {state.stamina}），操作被阻止")
            else:
                state.update_stamina(delta)
                logs.append(f"体力 {'+' if delta>0 else ''}{delta}")
                applied["stamina"] = state.stamina

        # 心情变动
        if "mood_delta" in updates and updates["mood_delta"] != 0:
            delta = int(updates["mood_delta"])
            state.update_mood(delta)
            logs.append(f"心情 {'+' if delta>0 else ''}{delta}")
            applied["mood"] = state.mood

        # 时间推进
        if "time_advance_min" in updates and updates["time_advance_min"] > 0:
            mins = int(updates["time_advance_min"])
            state.advance_time(mins)
            logs.append(f"时间推进 {mins} 分钟")
            applied["time"] = state.game_time

        system_msg = updates.get("reason", "状态自动更新") + "。" + "；".join(logs) if logs else updates.get("reason", "")
        return {
            "system_reply": system_msg,
            "applied_status": applied if applied else None
        }