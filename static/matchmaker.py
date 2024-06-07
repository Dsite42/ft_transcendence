from datetime import datetime
"""
#Matchmaker

Cases:
1. Player is waiting for a other player for a single game
2. Player is startig a single game with second player on the same keyboard
2. Player has created a turnement and is waiting for other players
3. Player has joined a turnement(joint from the list or got invitation) and is waiting for other players or turnement to start

Workflows:
1. Player creates a single game
1.2 Player sees the waiting screen
1.3 Player gets matched with another player
1.4 Player starts the game
1.5 Players finish the game see the result screen and game module sends the result to the matchmaker
1.6 Matchmaker updates the player stats and match history




"""

class turnement:
    def __init__(self, creator, turnement_name, turnement_size):
        self.creator = creator
        self.turnement_name = turnement_name
        self.turnement_size = turnement_size
        self.turnement_start_time = datetime.now()
        self.turnement_end_time = None
        self.players = []
        self.turnement_status = 'waiting'
        self.turnement_winner = None

    def join_turnement(self, player):
        if len(self.players) == self.turnement_size:
            return False
        self.players.append(player)

    def start_turnement(self):
        self.turnement_status = 'started'

    def abort_turnement(self):
        self.turnement_winner = None
        self.turnement_status = 'aborted'

    def end_turnement(self, winner):
        self.turnement_end_time = datetime.now()
        self.turnement_status = 'ended'
        self.turnement_winner = winner


class singleGame:
    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.game_start_time = datetime.now()
        self.game_end_time = None
        self.game_status = 'waiting'
        self.game_winner = None

    def join_game(self, player):
        if self.player2 is None:
            self.player2 = player
            return True
        return False
    
    def start_game(self):
        self.game_status = 'started'
    
    def end_game(self, winner):
        self.game_end_time = datetime.now()
        self.game_winner = winner
        self.game_status = 'ended'

    
    def abort_game(self):
        self.game_winner = None
        self.game_status = 'aborted'
        
    


class matchMaker:

    def __init__(self):
        self.turnements = []
        self.private_turnements = []
        self.single_games = []
        self.private_games = []

    def create_turnement(self, creator, turnement_name, turnement_size):
        new_turnement = turnement(creator, turnement_name, turnement_size)
        self.turnements.append(new_turnement)
        return new_turnement
    

    
def main():
    matchmaker = matchMaker()

    """
    def check_event(event, data):
        if event == 'new_signle_keyboard_game':
            new_single_keyboard_game = singleGame(player1, player2)
            new_single_keyboard_game.start_game()
            matchmaker.single_games.append(new_single_keyboard_game)
        if event == 'singleGame':
            for game in matchmaker.single_games:
                if game.player2 is None:
                    game.join_game(player2)
                    game.start_game()
                    return
            new_single_game = singleGame(player1, None)
            matchmaker.single_games.append(new_single_game)
        if event == 'create private game':
            new_private_game = singleGame(player1, None)
            matchmaker.private_games.append(new_private_game)
            #send the game id to the player
            return new_private_game 
        if event == 'join_private_game':
            game = matchmaker.private_games[game_id]
            game.join_game(player2)
            game.start_game()
        if event == 'turnement':
            for turnement in matchmaker.turnements:
                if turnement.turnement_status == 'waiting':
                    turnement.join_turnement(player)
                    if len(turnement.players) == turnement.turnement_size:
                        turnement.start_turnement()
                        return
            new_turnement = turnement(player, turnement_name, turnement_size)
            matchmaker.turnements.append(new_turnement)
            return new_turnement
        if event == 'join_private_turnement':
            turnement = matchmaker.turnements[turnement_id]
            turnement.join_turnement(player)
            if len(turnement.players) == turnement.turnement_size:
                turnement.start_turnement()
    """

    
    while True:
        check_event(event, data)
        

if __name__ == "__main__":
    main()