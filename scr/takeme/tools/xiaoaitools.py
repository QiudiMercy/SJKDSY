"""
注册给 LLM 的 Function Calling 工具定义
工具的描述必须清晰，让模型知道何时调用
"""
from typing import Optional, List

# 工具函数实现放在后面，这里先定义 schema

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "update_status",
            "description": "修改小爱的游戏状态数值（钱、体力、心情）或推进时间。只能修改当前游戏的状态。",
            "parameters": {
                "type": "object",
                "properties": {
                    "money_delta": {
                        "type": "integer",
                        "description": "金额变化（正数增加，负数减少），单位元"
                    },
                    "stamina_delta": {
                        "type": "integer",
                        "description": "体力变化（正数恢复，负数消耗），范围 -100 到 100"
                    },
                    "mood_delta": {
                        "type": "integer",
                        "description": "心情变化（正数提升，负数下降），范围 -100 到 100"
                    },
                    "time_advance_min": {
                        "type": "integer",
                        "description": "游戏内时间推进的分钟数"
                    },
                    "reason": {
                        "type": "string",
                        "description": "需要修改状态的原因，用于系统裁定日志"
                    }
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_poi",
            "description": "搜索成都的 POI 地点，可指定关键词或获取附近推荐",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，如'火锅'、'公园'，留空则返回附近推荐"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plan_route",
            "description": "规划从当前位置到目标地点不同交通方式的耗时与消耗",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_poi_uid": {
                        "type": "string",
                        "description": "目的地 POI 的 uid"
                    }
                },
                "required": ["target_poi_uid"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "chat_only",
            "description": "仅进行闲聊回复，不修改任何游戏状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "reply_text": {
                        "type": "string",
                        "description": "回复给用户的文本"
                    }
                },
                "required": ["reply_text"]
            }
        }
    }
]