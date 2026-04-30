from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class StateParams:
    """
    游戏状态参数
    """
    
    time: datetime = datetime(hour=8, minute=0) # 时间，8：00初始
    location: set = (104.26303659670522,30.560653968396135) # （经度，维度），默认成都东站
    mood: float = 100 # 情绪值，初始为100
    power: float = 100 # 体力值，初始为100
    money: float = 100 # 金钱，初始为100


class State:
    """
    状态类
    """

    def __init__(self, state_params: StateParams = None):
        self.state_params = state_params if state_params is not None else StateParams()
    
    @property
    def time(self) -> datetime:
        return self.state_params.time
    
    @property
    def location(self) -> set:
        return self.state_params.location
    
    @property
    def mood(self) -> float:
        return self.state_params.mood
    
    @property
    def power(self) -> float:
        return self.state_params.power
    
    @property
    def money(self) -> float:
        return self.state_params.money
    
    def modify_params(self, time=None, location=None, mood=None, power=None, money=None):
        """
        修改状态参数
        """
        if time is not None:
            self.state_params.time += timedelta(minutes=time)
        if location is not None:
            self.state_params.location += location
        if mood is not None:
            self.state_params.mood += mood
        if power is not None:
            self.state_params.power += power
        if money is not None:
            self.state_params.money += money
    
    @property
    def get_state(self) -> str:
        """
        返回当前参数状态
        """
        return f"当前参数状态如下：时间 {self.time}，位置 {self.location}，情绪 {self.mood}，体力 {self.power}，金钱 {self.money}"
