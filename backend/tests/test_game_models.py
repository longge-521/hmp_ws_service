# backend/tests/test_game_models.py
import pytest
from app.domain.game.entities import PlayerProfile, GameRecord


class TestPlayerProfile:
    def test_create_profile(self):
        p = PlayerProfile(player_id="p1", nickname="玩家1")
        assert p.beans == 10000  # 初始欢乐豆
        assert p.total_games == 0
        assert p.wins == 0

    def test_win_rate_zero_games(self):
        p = PlayerProfile(player_id="p1", nickname="玩家1")
        assert p.win_rate == 0.0

    def test_win_rate_calculation(self):
        p = PlayerProfile(player_id="p1", nickname="玩家1", total_games=10, wins=6)
        assert p.win_rate == 0.6


class TestGameRecord:
    def test_create_record(self):
        r = GameRecord(
            room_id="room_1", player_id="p1",
            role="landlord", result="win",
            score_change=60, multiplier=2
        )
        assert r.role == "landlord"
        assert r.result == "win"
