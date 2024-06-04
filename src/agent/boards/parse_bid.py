import re
from collections import defaultdict

import re
from collections import defaultdict

import re
from collections import defaultdict

import re

def parse_pbn_auction(file_path):
    with open(file_path, 'r') as file:
        pbn_contents = file.read()

    games = pbn_contents.split('[Event "')
    parsed_data = []

    for game in games[1:]:  # The first split element is empty or header info
        game_data = {
            'N': {'hand': None, 'bids': []},
            'E': {'hand': None, 'bids': []},
            'S': {'hand': None, 'bids': []},
            'W': {'hand': None, 'bids': []}
        }
        
        # Extract hands
        deal_pattern = r'\[Deal "([NSEW]):([^"]+)"\]'
        deal = re.search(deal_pattern, game)
        if deal:
            dealer = deal.group(1)
            hands = deal.group(2).split()
            for i, hand in enumerate(hands):
                position = "NESW"[(i + "NESW".index(dealer)) % 4]
                game_data[position]['hand'] = hand

        # Extract auction
        auction_pattern = r'\[Auction "([NSEW])"\](.*?)\[Play'
        auction = re.search(auction_pattern, game, re.S)
        if auction:
            dealer = auction.group(1)
            auction_sequence = auction.group(2).strip().split()
            positions = ["NESW"[("NESW".index(dealer) + j) % 4] for j in range(len(auction_sequence))]
            for i, bid in enumerate(auction_sequence):
                game_data[positions[i % 4]]['bids'].append(bid)

        parsed_data.append(game_data)

    return parsed_data


from collections import defaultdict

def analyze_bid_suit_presence(parsed_data):
    suit_ranks = {'A', 'K', 'Q', 'J'}
    bid_suit_presence = defaultdict(int)
    
    for game in parsed_data:
        for player in 'NESW':
            hand = game[player]['hand']
            bids = game[player]['bids']
            
            # Split the hand into suits
            suits = hand.split('.')
            suit_details = {
                'S': [card for card in suits[0] if card in suit_ranks],
                'H': [card for card in suits[1] if card in suit_ranks],
                'D': [card for card in suits[2] if card in suit_ranks],
                'C': [card for card in suits[3] if card in suit_ranks],
            }
            suit_counts = {
                'S': len(suits[0]),
                'H': len(suits[1]),
                'D': len(suits[2]),
                'C': len(suits[3]),
            }
            
            for bid in bids:
                if len(bid) <= 1:
                    continue
                if bid[1] in suit_details:
                    bid_suit = bid[1]
                    high_cards_in_suit = len(suit_details[bid_suit])
                    total_cards_in_suit = suit_counts[bid_suit]
                    bid_suit_presence[(high_cards_in_suit, total_cards_in_suit)] += 1

    return bid_suit_presence

# Example usage:
file_path = './agent/boards/tournaments/A1A10101.PBN'
parsed_auction_data = parse_pbn_auction(file_path)
bid_suit_presence = analyze_bid_suit_presence(parsed_auction_data)

import json
print(json.dumps(parsed_auction_data[:1], indent=2))
# print(json.dumps(bid_suit_presence, indent=2))
