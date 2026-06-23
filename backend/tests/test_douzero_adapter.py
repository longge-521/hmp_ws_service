import pytest
from app.domain.game.douzero_adapter import card_id_to_douzero, douzero_to_card_ids, get_obs_for_douzero

def test_card_translation_and_obs_generation():
    # Test card translation
    assert card_id_to_douzero(52) == 20  # Small Joker
    assert card_id_to_douzero(53) == 30  # Big Joker
    assert card_id_to_douzero(48) == 17  # Rank 2 (card ID 48 // 4 = 12)
    assert card_id_to_douzero(0) == 3    # Rank 3
    
    # Test translating back
    hand = [0, 1, 2, 52] # three 3s, small joker
    assert douzero_to_card_ids([3, 3], hand) == [0, 1]
    
    # Test obs generation shapes
    legal_actions = [[3], [3, 3]]
    play_history = [{"player": "landlord", "cards": [4]}] # single 4 played
    obs = get_obs_for_douzero(
        hand=hand,
        legal_actions=legal_actions,
        role="landlord",
        landlord_id="ai_bot_1",
        teammate_id="player_2",
        play_history=play_history
    )
    assert obs["x_batch"].shape == (2, 373)
    assert obs["z_batch"].shape == (2, 5, 162)
