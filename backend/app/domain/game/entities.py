# backend/app/domain/game/entities.py
"""游戏领域实体：玩家档案与对局记录"""
import datetime
from typing import Optional


class PlayerProfile:
    """玩家档案领域实体"""
    DEFAULT_BEANS = 10000

    def __init__(
        self,
        player_id: str,
        nickname: str,
        id: Optional[int] = None,
        beans: int = DEFAULT_BEANS,
        total_games: int = 0,
        wins: int = 0,
        created_at: Optional[datetime.datetime] = None,
    ):
        self.id = id
        self.player_id = player_id
        self.nickname = nickname
        self.beans = beans
        self.total_games = total_games
        self.wins = wins
        self.created_at = created_at or datetime.datetime.now()

    @property
    def win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return round(self.wins / self.total_games, 2)


class GameRecord:
    """对局记录领域实体"""

    def __init__(
        self,
        room_id: str,
        player_id: str,
        role: str,         # "landlord" / "farmer"
        result: str,        # "win" / "lose"
        score_change: int,
        multiplier: int,
        id: Optional[int] = None,
        created_at: Optional[datetime.datetime] = None,
    ):
        self.id = id
        self.room_id = room_id
        self.player_id = player_id
        self.role = role
        self.result = result
        self.score_change = score_change
        self.multiplier = multiplier
        self.created_at = created_at or datetime.datetime.now()
