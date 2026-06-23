from collections import Counter
from typing import List, Dict, Any
import numpy as np

# DouZero 的 rank 映射表
Card2Column = {3: 0, 4: 1, 5: 2, 6: 3, 7: 4, 8: 5, 9: 6, 10: 7,
               11: 8, 12: 9, 13: 10, 14: 11, 17: 12}

NumOnes2Array = {0: np.array([0, 0, 0, 0]),
                 1: np.array([1, 0, 0, 0]),
                 2: np.array([1, 1, 0, 0]),
                 3: np.array([1, 1, 1, 0]),
                 4: np.array([1, 1, 1, 1])}

# 整副牌的 DouZero 牌值，用来计算 other_hand_cards
deck_dz = []
for r in range(3, 15):
    deck_dz.extend([r] * 4)
deck_dz.extend([17] * 4)
deck_dz.extend([20, 30])

def card_id_to_douzero(card_id: int) -> int:
    if card_id == 52:
        return 20
    if card_id == 53:
        return 30
    rank = card_id // 4
    if rank == 12:
        return 17
    return rank + 3

def douzero_to_card_ids(action: List[int], hand: List[int]) -> List[int]:
    matched = []
    temp_hand = list(hand)
    for dz_val in action:
        found = False
        for cid in temp_hand:
            if card_id_to_douzero(cid) == dz_val:
                matched.append(cid)
                temp_hand.remove(cid)
                found = True
                break
        if not found:
            pass
    return matched

def _cards2array(list_cards):
    if len(list_cards) == 0:
        return np.zeros(54, dtype=np.int8)
    matrix = np.zeros([4, 13], dtype=np.int8)
    jokers = np.zeros(2, dtype=np.int8)
    counter = Counter(list_cards)
    for card, num_times in counter.items():
        if card < 20:
            matrix[:, Card2Column[card]] = NumOnes2Array[num_times]
        elif card == 20:
            jokers[0] = 1
        elif card == 30:
            jokers[1] = 1
    return np.concatenate((matrix.flatten('F'), jokers))

def _get_one_hot_array(num_left_cards, max_num_cards):
    one_hot = np.zeros(max_num_cards)
    num_left_cards = max(1, min(num_left_cards, max_num_cards))
    one_hot[num_left_cards - 1] = 1
    return one_hot

def _action_seq_list2array(action_seq_list):
    action_seq_array = np.zeros((len(action_seq_list), 54))
    for row, list_cards in enumerate(action_seq_list):
        action_seq_array[row, :] = _cards2array(list_cards)
    action_seq_array = action_seq_array.reshape(5, 162)
    return action_seq_array

def _process_action_seq(sequence, length=15):
    sequence = sequence[-length:].copy()
    if len(sequence) < length:
        empty_sequence = [[] for _ in range(length - len(sequence))]
        empty_sequence.extend(sequence)
        sequence = empty_sequence
    return sequence

def _get_one_hot_bomb(bomb_num):
    one_hot = np.zeros(15)
    bomb_num = max(0, min(bomb_num, 14))
    one_hot[bomb_num] = 1
    return one_hot

class InfosetMock:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def _get_obs_landlord(infoset):
    num_legal_actions = len(infoset.legal_actions)
    my_handcards = _cards2array(infoset.player_hand_cards)
    my_handcards_batch = np.repeat(my_handcards[np.newaxis, :], num_legal_actions, axis=0)

    other_handcards = _cards2array(infoset.other_hand_cards)
    other_handcards_batch = np.repeat(other_handcards[np.newaxis, :], num_legal_actions, axis=0)

    last_action = _cards2array(infoset.last_move)
    last_action_batch = np.repeat(last_action[np.newaxis, :], num_legal_actions, axis=0)

    my_action_batch = np.zeros(my_handcards_batch.shape)
    for j, action in enumerate(infoset.legal_actions):
        my_action_batch[j, :] = _cards2array(action)

    landlord_up_num_cards_left = _get_one_hot_array(infoset.num_cards_left_dict['landlord_up'], 17)
    landlord_up_num_cards_left_batch = np.repeat(landlord_up_num_cards_left[np.newaxis, :], num_legal_actions, axis=0)

    landlord_down_num_cards_left = _get_one_hot_array(infoset.num_cards_left_dict['landlord_down'], 17)
    landlord_down_num_cards_left_batch = np.repeat(landlord_down_num_cards_left[np.newaxis, :], num_legal_actions, axis=0)

    landlord_up_played_cards = _cards2array(infoset.played_cards['landlord_up'])
    landlord_up_played_cards_batch = np.repeat(landlord_up_played_cards[np.newaxis, :], num_legal_actions, axis=0)

    landlord_down_played_cards = _cards2array(infoset.played_cards['landlord_down'])
    landlord_down_played_cards_batch = np.repeat(landlord_down_played_cards[np.newaxis, :], num_legal_actions, axis=0)

    bomb_num = _get_one_hot_bomb(infoset.bomb_num)
    bomb_num_batch = np.repeat(bomb_num[np.newaxis, :], num_legal_actions, axis=0)

    x_batch = np.hstack((my_handcards_batch,
                         other_handcards_batch,
                         last_action_batch,
                         landlord_up_played_cards_batch,
                         landlord_down_played_cards_batch,
                         landlord_up_num_cards_left_batch,
                         landlord_down_num_cards_left_batch,
                         bomb_num_batch,
                         my_action_batch))
                         
    x_no_action = np.hstack((my_handcards,
                             other_handcards,
                             last_action,
                             landlord_up_played_cards,
                             landlord_down_played_cards,
                             landlord_up_num_cards_left,
                             landlord_down_num_cards_left,
                             bomb_num))
                             
    z = _action_seq_list2array(_process_action_seq(infoset.card_play_action_seq))
    z_batch = np.repeat(z[np.newaxis, :, :], num_legal_actions, axis=0)
    
    return {
        'position': 'landlord',
        'x_batch': x_batch.astype(np.float32),
        'z_batch': z_batch.astype(np.float32),
        'legal_actions': infoset.legal_actions,
        'x_no_action': x_no_action.astype(np.int8),
        'z': z.astype(np.int8),
    }

def _get_obs_landlord_up(infoset):
    num_legal_actions = len(infoset.legal_actions)
    my_handcards = _cards2array(infoset.player_hand_cards)
    my_handcards_batch = np.repeat(my_handcards[np.newaxis, :], num_legal_actions, axis=0)

    other_handcards = _cards2array(infoset.other_hand_cards)
    other_handcards_batch = np.repeat(other_handcards[np.newaxis, :], num_legal_actions, axis=0)

    last_action = _cards2array(infoset.last_move)
    last_action_batch = np.repeat(last_action[np.newaxis, :], num_legal_actions, axis=0)

    my_action_batch = np.zeros(my_handcards_batch.shape)
    for j, action in enumerate(infoset.legal_actions):
        my_action_batch[j, :] = _cards2array(action)

    last_landlord_action = _cards2array(infoset.last_move_dict['landlord'])
    last_landlord_action_batch = np.repeat(last_landlord_action[np.newaxis, :], num_legal_actions, axis=0)
    
    landlord_num_cards_left = _get_one_hot_array(infoset.num_cards_left_dict['landlord'], 20)
    landlord_num_cards_left_batch = np.repeat(landlord_num_cards_left[np.newaxis, :], num_legal_actions, axis=0)

    landlord_played_cards = _cards2array(infoset.played_cards['landlord'])
    landlord_played_cards_batch = np.repeat(landlord_played_cards[np.newaxis, :], num_legal_actions, axis=0)

    last_teammate_action = _cards2array(infoset.last_move_dict['landlord_down'])
    last_teammate_action_batch = np.repeat(last_teammate_action[np.newaxis, :], num_legal_actions, axis=0)
    
    teammate_num_cards_left = _get_one_hot_array(infoset.num_cards_left_dict['landlord_down'], 17)
    teammate_num_cards_left_batch = np.repeat(teammate_num_cards_left[np.newaxis, :], num_legal_actions, axis=0)

    teammate_played_cards = _cards2array(infoset.played_cards['landlord_down'])
    teammate_played_cards_batch = np.repeat(teammate_played_cards[np.newaxis, :], num_legal_actions, axis=0)

    bomb_num = _get_one_hot_bomb(infoset.bomb_num)
    bomb_num_batch = np.repeat(bomb_num[np.newaxis, :], num_legal_actions, axis=0)

    x_batch = np.hstack((my_handcards_batch,
                         other_handcards_batch,
                         landlord_played_cards_batch,
                         teammate_played_cards_batch,
                         last_action_batch,
                         last_landlord_action_batch,
                         last_teammate_action_batch,
                         landlord_num_cards_left_batch,
                         teammate_num_cards_left_batch,
                         bomb_num_batch,
                         my_action_batch))
                         
    x_no_action = np.hstack((my_handcards,
                             other_handcards,
                             landlord_played_cards,
                             teammate_played_cards,
                             last_action,
                             last_landlord_action,
                             last_teammate_action,
                             landlord_num_cards_left,
                             teammate_num_cards_left,
                             bomb_num))
                             
    z = _action_seq_list2array(_process_action_seq(infoset.card_play_action_seq))
    z_batch = np.repeat(z[np.newaxis, :, :], num_legal_actions, axis=0)
    
    return {
        'position': 'landlord_up',
        'x_batch': x_batch.astype(np.float32),
        'z_batch': z_batch.astype(np.float32),
        'legal_actions': infoset.legal_actions,
        'x_no_action': x_no_action.astype(np.int8),
        'z': z.astype(np.int8),
    }

def _get_obs_landlord_down(infoset):
    num_legal_actions = len(infoset.legal_actions)
    my_handcards = _cards2array(infoset.player_hand_cards)
    my_handcards_batch = np.repeat(my_handcards[np.newaxis, :], num_legal_actions, axis=0)

    other_handcards = _cards2array(infoset.other_hand_cards)
    other_handcards_batch = np.repeat(other_handcards[np.newaxis, :], num_legal_actions, axis=0)

    last_action = _cards2array(infoset.last_move)
    last_action_batch = np.repeat(last_action[np.newaxis, :], num_legal_actions, axis=0)

    my_action_batch = np.zeros(my_handcards_batch.shape)
    for j, action in enumerate(infoset.legal_actions):
        my_action_batch[j, :] = _cards2array(action)

    last_landlord_action = _cards2array(infoset.last_move_dict['landlord'])
    last_landlord_action_batch = np.repeat(last_landlord_action[np.newaxis, :], num_legal_actions, axis=0)
    
    landlord_num_cards_left = _get_one_hot_array(infoset.num_cards_left_dict['landlord'], 20)
    landlord_num_cards_left_batch = np.repeat(landlord_num_cards_left[np.newaxis, :], num_legal_actions, axis=0)

    landlord_played_cards = _cards2array(infoset.played_cards['landlord'])
    landlord_played_cards_batch = np.repeat(landlord_played_cards[np.newaxis, :], num_legal_actions, axis=0)

    last_teammate_action = _cards2array(infoset.last_move_dict['landlord_up'])
    last_teammate_action_batch = np.repeat(last_teammate_action[np.newaxis, :], num_legal_actions, axis=0)
    
    teammate_num_cards_left = _get_one_hot_array(infoset.num_cards_left_dict['landlord_up'], 17)
    teammate_num_cards_left_batch = np.repeat(teammate_num_cards_left[np.newaxis, :], num_legal_actions, axis=0)

    teammate_played_cards = _cards2array(infoset.played_cards['landlord_up'])
    teammate_played_cards_batch = np.repeat(teammate_played_cards[np.newaxis, :], num_legal_actions, axis=0)

    bomb_num = _get_one_hot_bomb(infoset.bomb_num)
    bomb_num_batch = np.repeat(bomb_num[np.newaxis, :], num_legal_actions, axis=0)

    x_batch = np.hstack((my_handcards_batch,
                         other_handcards_batch,
                         landlord_played_cards_batch,
                         teammate_played_cards_batch,
                         last_action_batch,
                         last_landlord_action_batch,
                         last_teammate_action_batch,
                         landlord_num_cards_left_batch,
                         teammate_num_cards_left_batch,
                         bomb_num_batch,
                         my_action_batch))
                         
    x_no_action = np.hstack((my_handcards,
                             other_handcards,
                             landlord_played_cards,
                             teammate_played_cards,
                             last_action,
                             last_landlord_action,
                             last_teammate_action,
                             landlord_num_cards_left,
                             teammate_num_cards_left,
                             bomb_num))
                             
    z = _action_seq_list2array(_process_action_seq(infoset.card_play_action_seq))
    z_batch = np.repeat(z[np.newaxis, :, :], num_legal_actions, axis=0)
    
    return {
        'position': 'landlord_down',
        'x_batch': x_batch.astype(np.float32),
        'z_batch': z_batch.astype(np.float32),
        'legal_actions': infoset.legal_actions,
        'x_no_action': x_no_action.astype(np.int8),
        'z': z.astype(np.int8),
    }

def convert_action_to_douzero(action: List[int], hand_card_ids: List[int]) -> List[int]:
    if not action:
        return []
    if any(x > 30 for x in action) or all(x in hand_card_ids for x in action):
        return [card_id_to_douzero(c) for c in action]
    return action

def convert_cards_to_douzero(cards: List[int]) -> List[int]:
    if not cards:
        return []
    if any(x > 30 for x in cards):
        return [card_id_to_douzero(c) for c in cards]
    if any(x in (0, 1, 2) for x in cards):
        return [card_id_to_douzero(c) for c in cards]
    return cards

def determine_role(player_id: str, landlord_id: str, teammate_id: str, current_role: str, play_history: List[dict]) -> str:
    if player_id in ("landlord", "landlord_up", "landlord_down"):
        return player_id
    if player_id == landlord_id:
        return "landlord"
    if current_role != "landlord":
        if player_id == teammate_id:
            return "landlord_down" if current_role == "landlord_up" else "landlord_up"
        else:
            return current_role
            
    landlord_down_id = None
    for i, record in enumerate(play_history):
        pid = record["player"]
        if pid == landlord_id or pid == "landlord":
            for j in range(i + 1, len(play_history)):
                next_pid = play_history[j]["player"]
                if next_pid != landlord_id and next_pid != "landlord":
                    landlord_down_id = next_pid
                    break
            if landlord_down_id is not None:
                break
                
    if landlord_down_id is not None:
        if player_id == landlord_down_id:
            return "landlord_down"
        return "landlord_up"
        
    if teammate_id and teammate_id != landlord_id:
        if player_id == teammate_id:
            return "landlord_down"
        return "landlord_up"
        
    return "landlord_down"

def get_obs_for_douzero(
    hand: List[int],
    legal_actions: List[List[int]],
    role: str,
    landlord_id: str,
    teammate_id: str,
    play_history: List[dict]
) -> dict:
    # 1. 转换手牌和合法动作
    my_hand_dz = [card_id_to_douzero(c) for c in hand]
    legal_actions_dz = [convert_action_to_douzero(act, hand) for act in legal_actions]
    
    # 2. 还原局势
    played_cards = {"landlord": [], "landlord_up": [], "landlord_down": []}
    last_move_dict = {"landlord": [], "landlord_up": [], "landlord_down": []}
    num_cards_left = {"landlord": 20, "landlord_up": 17, "landlord_down": 17}
    last_move = []
    bomb_num = 0
    card_play_action_seq = []
    
    for record in play_history:
        pid = record["player"]
        cards_dz = convert_cards_to_douzero(record["cards"])
        p_role = determine_role(pid, landlord_id, teammate_id, role, play_history)
        
        played_cards[p_role].extend(cards_dz)
        last_move_dict[p_role] = cards_dz
        num_cards_left[p_role] -= len(cards_dz)
        if len(cards_dz) > 0:
            last_move = cards_dz
            
        # 炸弹检测
        is_bomb = False
        if len(cards_dz) == 2 and set(cards_dz) == {20, 30}:
            is_bomb = True
        elif len(cards_dz) == 4 and len(set(cards_dz)) == 1:
            is_bomb = True
        if is_bomb:
            bomb_num += 1
            
        card_play_action_seq.append(cards_dz)
        
    # 3. 计算 other_hand_cards (未公开的牌)
    deck_counter = Counter(deck_dz)
    my_hand_counter = Counter(my_hand_dz)
    all_played_cards_dz = []
    for rc in played_cards.values():
        all_played_cards_dz.extend(rc)
    played_counter = Counter(all_played_cards_dz)
    
    other_counter = deck_counter - my_hand_counter - played_counter
    other_hand_cards = []
    for card, count in other_counter.items():
        if count > 0:
            other_hand_cards.extend([card] * count)
    other_hand_cards.sort()
    
    # 4. 包装成 InfosetMock
    infoset = InfosetMock(
        player_position=role,
        player_hand_cards=my_hand_dz,
        legal_actions=legal_actions_dz,
        other_hand_cards=other_hand_cards,
        last_move=last_move,
        num_cards_left_dict=num_cards_left,
        played_cards=played_cards,
        bomb_num=bomb_num,
        card_play_action_seq=card_play_action_seq,
        last_move_dict=last_move_dict
    )
    
    # 5. 调用各自的特征构造函数
    if role == 'landlord':
        return _get_obs_landlord(infoset)
    elif role == 'landlord_up':
        return _get_obs_landlord_up(infoset)
    elif role == 'landlord_down':
        return _get_obs_landlord_down(infoset)
    else:
        raise ValueError(f"Invalid role: {role}")
