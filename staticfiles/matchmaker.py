from datetime import datetime
"""
#Matchmaker

Databases/ Tables
- Users (intra_id, player_name, player_stats{score, wins, loses, winrate}, game_history(relation to Game Databases/ Tables), tournament_history(relation to Game Databases/ Tables))
- Games (game_id, player1, player2, game_start_time, game_end_time, game_winner, p1_wins, p2_wins)
- Tournaments (tournament_id, creator, tournament_name, tournament_size, tournament_start_time, tournament_end_time, tournament_winner, games{game1, game2,..}, players{player1, player2, ...})


Cases:
1. Player is waiting for a other player for a single game
2. Player is startig a single game with second player on the same keyboard
2. Player has created a tournament and is waiting for other players
3. Player has joined a tournament(joint from the list) and is waiting for other players or tournament to start

Workflow single game:
1. Player creates a single game
    1.1 Client opens a websocket connection to the matchmaker 
    1.2 Player sees the waiting screen (client side matchmaker status(singelton siehe jonas repo))
2. Matchmaker
    2.0 Matchmaker checks process_request(override) if it is a valid websocket connection
    2.1 Matchmaker checks if there is a waiting game
        2.1.1 Matchmaker creates a single game object
        2.1.2 Matchmaker requests via rpc a game address from the game service
    2.2 Matchmaker sends via websocket the game address to the two players
3. Players connect to the game and start playing
4. Game service sends the result via rpc to the matchmaker
5. Matchmaker updates the player stats and match database

- disconnect handling? -> if game aborted game service calls matchmaker abrot function

Workflow tournament:
1. Player creates a tournament
    1.1 Client opens a websocket connection to the matchmaker
    1.2 Player sees the waiting screen
2. Matchmaker
    2.1 Matchmaker creates a tournament object
    2.2 Matchmaker is waiting for other players to join
    2.3 Matchmaker checks if the tournament is complete and create match combinations
    2.4 Matchmaker requests via rpc a game address from the game service if the tournament is complete
    2.5 Matchmaker sends via websocket the game address to the first two players
3. Players connect to the game and start playing
4. Game service sends the result to the matchmaker
5. Matchmaker
    5.1 Matchmaker saves the game match result
    5.2 Matchmaker goes to the next tournament match
    5.3 Matchmaker requests via rpc a game address from the game service
    5.4 Matchmaker sends via websocket the game address to the next two players
6. Repeat 3-5 until the tournament is finished
7. Matchmaker
    7.1 Matchmaker checks if there is a winner
    7.2 If not Matchmaker creates new matches and goes to 5.2
    7.3 If yes Matchmaker updates the player stats, game database and the tournament database
    7.4 Matchmaker sends to the clients a redirect to the tournament result page


- disconnect handling?
- neues game darf erst angefagt werden, wenn zwei spieler vorhanden sind




game_service interface:
matchmaker => game_service
- create_keyboard_game(player1, guest) - creates a single game with two players on the same keyboard
- create_game(game_id, player1, player2) 


game_service => matchmaker
- keyboard game stats werden nicht erfasst
- transmit_game_result(game_id, winner, p1_wins, p2_wins) # game aborded if winner -1 and 0, 0




"""

class tournament:
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
        self.single_games = []
        self.keyboard_games = []

    def create_turnement(self, creator, turnement_name, turnement_size):
        new_turnement = tournament(creator, turnement_name, turnement_size)
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
        if event == 'tournament':
            for tournament in matchmaker.turnements:
                if tournament.turnement_status == 'waiting':
                    tournament.join_turnement(player)
                    if len(tournament.players) == tournament.turnement_size:
                        tournament.start_turnement()
                        return
            new_turnement = tournament(player, turnement_name, turnement_size)
            matchmaker.turnements.append(new_turnement)
            return new_turnement
    """

    
    while True:
        check_event(event, data)
        

if __name__ == "__main__":
    main()