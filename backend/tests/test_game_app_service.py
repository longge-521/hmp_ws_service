# backend/tests/test_game_app_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.application.game.game_app_service import GameAppService
from app.domain.game.room import GameRoom, Player, GamePhase


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.get_player_room = AsyncMock(return_value=None)
    repo.get_match_queue_length = AsyncMock(return_value=0)
    repo.add_to_match_queue = AsyncMock()
    repo.remove_from_match_queue = AsyncMock()
    repo.set_player_room = AsyncMock()
    repo.save_room = AsyncMock()
    repo.get_room = AsyncMock(return_value=None)
    repo.pop_match_players = AsyncMock(return_value=[])
    repo.delete_room = AsyncMock()
    repo.remove_player_room = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repo):
    return GameAppService(mock_repo)


class TestGameAppService:

    @pytest.mark.asyncio
    async def test_join_match_adds_to_queue(self, service, mock_repo):
        """加入匹配应添加到队列"""
        mock_repo.pop_match_players.return_value = ["p1"]  # 不够3人
        result = await service.join_match("p1", "玩家1")
        mock_repo.add_to_match_queue.assert_called_once_with("p1")

    @pytest.mark.asyncio
    async def test_join_match_already_in_room(self, service, mock_repo):
        """已在房间中的玩家不能再匹配"""
        mock_repo.get_player_room.return_value = "room_existing"
        result = await service.join_match("p1", "玩家1")
        assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_cancel_match(self, service, mock_repo):
        """取消匹配应从队列移除"""
        result = await service.cancel_match("p1")
        mock_repo.remove_from_match_queue.assert_called_once_with("p1")
