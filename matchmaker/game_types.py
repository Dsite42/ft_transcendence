from datetime import datetime
from itertools import combinations
from . import my_global_vars


# Tournament class for handling tournaments   
class Tournament:
    def __init__(self, tournament_id, creator, tournament_name, number_of_players):
        self.id = tournament_id
        self.creator = creator
        self.name = tournament_name
        self.number_of_players = number_of_players
        self.start_time = datetime.now()
        self.end_time = None
        self.players = []
        self.display_names = {}
        self.matches = []
        self.current_match_index = 0
        self.status = 'waiting'
        self.winner = None

    def join_tournament(self, player_id):
        if player_id in self.players:
            return -1
        elif len(self.players) < self.number_of_players:
            self.players.append(player_id)
            return 1
        return 0
    
    def generate_matches(self):
        self.matches = []
        for match in combinations(self.players, 2):
            my_global_vars.game_id_counter += 1
            self.matches.append({'id': my_global_vars.game_id_counter, 'players': match, 'status': 'pending', 'winner': None, 'p1_wins': None, 'p2_wins': None})

    def add_draw_matches(self, draw_players):
        for match in combinations(draw_players, 2):
            my_global_vars.game_id_counter += 1
            self.matches.append({'id': my_global_vars.game_id_counter, 'players': match, 'status': 'pending', 'winner': None, 'p1_wins': None, 'p2_wins': None})

    def start_tournament(self):
        self.status = 'ongoing'
        self.generate_matches()

    def change_match_status(self, match_index, status):
        if 0 <= match_index < len(self.matches):
            self.matches[match_index]['status'] = status


    def update_match_result(self, match_index, winner, p1_wins, p2_wins):
        if 0 <= match_index < len(self.matches):
            self.matches[match_index]['status'] = 'completed'
            self.matches[match_index]['winner'] = winner
            self.matches[match_index]['p1_wins'] = p1_wins
            self.matches[match_index]['p2_wins'] = p2_wins
            self.current_match_index += 1
            if self.current_match_index >= len(self.matches):
                self.end_tournament()

    def calculate_winner(self):
        win_counts = {player: 0 for player in self.players}
        for match in self.matches:
            if match['winner'] is not None:
                win_counts[match['winner']] += 1
        # check if we have several players with the maximum number of wins
        max_wins = max(win_counts.values())
        if list(win_counts.values()).count(max_wins) > 1:
            draw_players = [player for player, wins in win_counts.items() if wins == max_wins]
            self.add_draw_matches(draw_players)
            return False
        else:
            self.winner = max(win_counts, key=win_counts.get)
            return True

    def abort_tournament(self):
        self.winner = None
        self.status = 'aborted'

    def end_tournament(self):
        if self.calculate_winner():
            self.end_time = datetime.now()
            self.status = 'ended'
            return True
        else:
            return False
    
    def to_dict(self):
        serialized_data = {
            'id': self.id,
            'creator': self.creator,
            'name': self.name,
            'number_of_players': self.number_of_players,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'players': self.players,
            'display_names': self.display_names,
            'status': self.status,
            'winner': self.winner,
            'matches': self.matches,
            'current_match_index': self.current_match_index,
        }
        return serialized_data

# SingleGame class for handling single games
class SingleGame:
    def __init__(self, game_id, player1, client1, player2, client2, game_address):
        self.game_id = game_id
        self.game_address = game_address
        self.player1 = player1
        self.client1 = client1
        self.player2 = player2
        self.client2 = client2
        self.game_start_time = datetime.now()
        self.game_end_time = None
        self.game_status = 'waiting'
        self.game_winner = None
        self.p1_wins = None
        self.p2_wins = None

    def join_game(self, player):
        if self.player2 is None:
            self.player2 = player
            return True
        return False
    
    def start_game(self):
        self.game_status = 'started'
    
    def end_game(self, winner, p1_wins, p2_wins):
        self.game_end_time = datetime.now()
        self.game_winner = winner
        self.p1_wins = p1_wins
        self.p2_wins = p2_wins
        self.game_status = 'ended'
    
    def abort_game(self):
        self.game_winner = None
        self.game_status = 'aborted'

