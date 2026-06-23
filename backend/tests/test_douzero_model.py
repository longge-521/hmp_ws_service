import pytest
import torch
from app.domain.game.douzero_model import DouZeroAgentManager, LandlordLstmModel

def test_model_definitions_and_inference():
    # Test Model Structure
    landlord_model = LandlordLstmModel()
    dummy_z = torch.zeros(1, 5, 162)
    dummy_x = torch.zeros(1, 373)
    out = landlord_model(dummy_z, dummy_x)
    assert out.shape == (1, 1)

    # Test Manager Fallback when weights are missing
    manager = DouZeroAgentManager()
    assert manager.is_available() is False
