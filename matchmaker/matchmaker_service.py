import asyncio
from asyncio import Future
import json

import django
from django.conf import settings
from django.db import models, connections

from aiorpc import AioRPC
import pika
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.dispatch import public, RPCDispatcher
from tinyrpc.transports.rabbitmq import RabbitMQClientTransport
from tinyrpc import RPCClient

import websockets
from websockets.exceptions import ConnectionClosed
from asgiref.sync import sync_to_async
from datetime import datetime

from itertools import combinations


# Class definitions

# Client class for handling clients
class Client:
    def __init__(self, player_id, websocket):
        self.player_id = player_id
        self.websocket = websocket

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
        if len(self.players) < self.number_of_players:
            self.players.append(player_id)
            return True
        return False
    
    def generate_matches(self):
        global game_id_counter
        self.matches = []
        for match in combinations(self.players, 2):
            game_id_counter += 1
            self.matches.append({'id': game_id_counter, 'players': match, 'status': 'pending', 'winner': None, 'p1_wins': None, 'p2_wins': None})

    def add_draw_matches(self, draw_players):
        global game_id_counter
        for match in combinations(draw_players, 2):
            game_id_counter += 1
            self.matches.append({'id': game_id_counter, 'players': match, 'status': 'pending', 'winner': None, 'p1_wins': None, 'p2_wins': None})

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


# Database class for handling database operations via Django database connection
class Database:
    def __init__(self, engine='django.db.backends.sqlite3', name=None, user=None, password=None, host=None, port=None):
        self.Model = None

        databases = {
            'default': {
                'ENGINE': engine,
                'NAME': name,
                'USER': 'chris',
                'PASSWORD': 'chris',
                'HOST': '127.0.0.1',
                'PORT': '8000',
                'APP_LABEL': 'frontapp',
            }
        }

        settings.configure(DATABASES=databases)
        django.setup()

        class CustomBaseModel(models.Model):
            class Meta:
                app_label = 'frontapp'
                abstract = True

        self.Model = CustomBaseModel


    def game_result_to_user_stats(self, player_id, is_winner, p2_wins, score):
        print(f"game_result_to_user_stats: Player ID: {player_id}, is_winner: {is_winner}, p2_wins: {p2_wins}, score: {score}")
        sql_query = "SELECT stats FROM auth_user WHERE id = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [player_id])
            print(f"Player ID: {player_id}")
            stats = cursor.fetchone()[0]

        stats = json.loads(stats)
        stats['games_played'] = stats.get('games_played', 0) + 1
        if is_winner == 1:
            stats['games_won'] = stats.get('games_won', 0) + 1
        else:
            stats['games_lost'] = stats.get('games_lost', 0) + 1
        if score:
            stats['score'] = stats.get('score', 0) + score
        stats = json.dumps(stats)

        sql_query = "UPDATE auth_user SET stats = %s WHERE id = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [stats, player_id])

    def add_game(self, player1, player2, winner, p1_wins, p2_wins):
        sql_query = """
        INSERT INTO frontapp_game (player1_id, player2_id, winner_id, p1_wins, p2_wins, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        current_time = datetime.now()
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, (player1, player2, winner, p1_wins, p2_wins, current_time))

    def add_tournament(self, tournament: Tournament):
        sql_query = """
        INSERT INTO frontapp_tournament (creator_id, name, number_of_players, start_time, status, winner_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, (tournament.creator, tournament.name, tournament.number_of_players, tournament.start_time, tournament.status, tournament.winner))
            inserted_row_id = cursor.lastrowid
        return inserted_row_id
    
    def delete_tournament(self, tournament_id):
        print(f"Deleting tournament {tournament_id}")
        # First, delete any dependent Tournament-customuser relationships for this tournament
        delete_relationships_sql = "DELETE FROM frontapp_tournament_players WHERE tournament_id = %s;"
        # Then, delete the tournament
        delete_tournament_sql = "DELETE FROM frontapp_tournament WHERE id = %s;"
        
        with connections['default'].cursor() as cursor:
            cursor.execute(delete_relationships_sql, [tournament_id])
            cursor.execute(delete_tournament_sql, [tournament_id])
    
    # On game_service start, all open tournaments in the db are deleted, because they can not be handled anymore and are invalid
    def delete_all_tournaments(self):
        # First, delete any dependent Tournament-customuser relationships
        delete_relationships_sql = "DELETE FROM frontapp_tournament_players WHERE tournament_id IN (SELECT id FROM frontapp_tournament);"
        # Then, delete the tournaments
        delete_tournaments_sql = "DELETE FROM frontapp_tournament;"
        
        with connections['default'].cursor() as cursor:
            cursor.execute(delete_relationships_sql)
            cursor.execute(delete_tournaments_sql)

    def change_tournament_status(self, tournament_id, status):
        sql_query = "UPDATE frontapp_tournament SET status = %s WHERE id = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [status, tournament_id])

    def get_display_names(self, player_ids):
        # Generate placeholders for each item in player_ids
        placeholders = ','.join(['%s'] * len(player_ids))
        sql_query = f"SELECT id, display_name FROM auth_user WHERE id IN ({placeholders});"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, player_ids)
            result = {row[0]: row[1] for row in cursor.fetchall()}
        return result
    
    def get_display_name(self, player_id):
        sql_query = "SELECT display_name FROM auth_user WHERE id = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [player_id])
            result = cursor.fetchone()
        return result[0] if result else None

    def add_player_to_tournament(self, tournament_id, player_id):
        print(f"Adding players to tournament {tournament_id}: {player_id}")
        join_table = 'tournament_players'
        tournament_col = 'tournament_id'
        player_col = 'customuser_id'
        sql_query = f"INSERT INTO frontapp_{join_table} ({tournament_col}, {player_col}) VALUES (%s, %s);"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [tournament_id, player_id])
        
# The MatchMaker class handles the matchmaking process for keyboard games, single games and tournaments. It is the main service that communicates with the game_service and the clients.    
class MatchMaker:
    def __init__(self):
        self.db = Database(engine='django.db.backends.sqlite3', name='/home/cgodecke/Desktop/Core/ft_transcendence/frontend_draft/db.sqlite3')
        self.db.delete_all_tournaments()
        self.tournaments = []
        self.single_games = []
        self.single_games_queue = []

    # Creates a new tournament and sends the tournament ID to the creator
    async def create_tournament(self, creator, tournament_name, number_of_players):
        new_tournament = Tournament(0, creator, tournament_name, number_of_players)
        new_tournament.id = await sync_to_async(self.db.add_tournament)(new_tournament)
        self.tournaments.append(new_tournament)
        message = {
            'action': 'tournament_created',
            'message': f'tournament successfully created. ID: ',
            'tournament_id': new_tournament.id,
        }
        await send_message_to_client(creator, message)

        print(f"Tournament created: id {new_tournament.id} name: {new_tournament.name}, creator: {new_tournament.creator}, size: {new_tournament.number_of_players}")
    
    # Checks if a tournament is ready to start
    async def check_tournament_readyness(self, tournament):
        if len(tournament.players) == tournament.number_of_players:
            tournament.start_tournament()
            tournament.change_match_status(0, 'ongoing')
            await sync_to_async(self.db.change_tournament_status)(tournament.id, 'ongoing')
            message = {
                'action': 'tournament_started',
                'message': f'Tournament {tournament.id} has started.',
                'tournament_id': tournament.id,
                'tournament' : tournament.to_dict()
            }
            for player in tournament.players:
                await send_message_to_client(player, message)
            print(f"Tournament {tournament.id} has started.")
            print(f"Match_id: {tournament.matches[0]['id']}, player1: {tournament.matches[0]['players'][0]}, player2: {tournament.matches[0]['players'][1]}")
            await self.start_tournament_match(tournament.matches[0]['id'], tournament.matches[0]['players'][0], tournament.matches[0]['players'][1])

    # Requests via game_service a new tournament match and sends the game address to the players
    async def start_tournament_match(self, game_id, player1_id, player2_id):
        print(f'Creating tournament match between Player {player1_id} and Player {player2_id}.')
        result = await sync_to_async(matchmaker_service.game_service.create_game)(game_id, player1_id, player2_id)
        game_address = result['game_address']
        message = {
            'action': 'game_address',
            'message': f'Tournament match successfully created. Join via: ',
            'game_address': game_address,
        }
        client1, client2 = await self.search_single_game_clients(player1_id, player2_id)
        if not client1 or not client2:
            print("Error: Could not find both clients.")
            return
        
        await send_message_to_client(player1_id, message)
        await send_message_to_client(player2_id, message)
        
    # Adds a player to a tournament and checks if the tournament is full
    async def join_tournament(self, player_id, tournament_id):
        tournament = None
        for t in self.tournaments:
            if t.id == tournament_id:
                tournament = t
                break
        if tournament is not None:
            if tournament.join_tournament(player_id):
                tournament.display_names[player_id] = await sync_to_async(self.db.get_display_name)(player_id)
                message = {
                    'action': 'tournament_joined',
                    'message': f'Player {player_id} successfully joined tournament {tournament_id}.',
                    'tournament_id': tournament.id,
                    'tournament': tournament.to_dict()
                }
                await sync_to_async(self.db.add_player_to_tournament)(tournament_id, player_id)
                if len(tournament.players) < tournament.number_of_players:
                    await send_message_to_client(player_id, message)
                print(f"Player {player_id} joined tournament {tournament_id}.")
                await self.check_tournament_readyness(tournament)
            else:
                message = {
                    'action': 'tournament_full',
                    'message': f'Tournament {tournament_id} is full.',
                }
                await send_message_to_client(player_id, message)
                print(f"Tournament {tournament_id} is full.")
        else:
            message = {
                'action': 'tournament_not_found',
                'message': f'Tournament {tournament_id} not found.',
            }
            await send_message_to_client(player_id, message)
            print(f"Tournament {tournament_id} not found.")

    # Adds a player to the single game queue and checks if there are enough players to start a game
    async def request_single_game(self, player1):
        self.single_games_queue.append(player1)
        await self.check_single_game_queue()

    # Forwards the request to create a keyboard game
    async def request_keyboard_game(self, player1):
        await self.create_keyboard_game(player1)

    # Checks if there are enough players in the queue to start a single game
    async def check_single_game_queue(self):
        print(f'Checking single game queue. Length: {len(self.single_games_queue)}')
        if len(self.single_games_queue) >= 2:
            player1 = self.single_games_queue.pop(0)
            player2 = self.single_games_queue.pop(0)
            await self.create_single_game(player1, player2)


    async def search_single_game_clients(self, player1_id, player2_id):
        client1 = connected_clients.get(player1_id)
        client2 = connected_clients.get(player2_id)
        if client1 and client2:
            return client1, client2
        return None, None

    # Requests via game_service a new (single) game address and sends it to the players
    async def create_single_game(self, player1_id, player2_id):
        print(f'Creating single game between Player {player1_id} and Player {player2_id}.')
        global game_id_counter
        game_id = game_id_counter
        game_id_counter += 1
        result = await sync_to_async(matchmaker_service.game_service.create_game)(game_id, player1_id, player2_id)
        game_address = result['game_address']
        message = {
            'action': 'game_address',
            'message': f'Game successfully created. Join via: ',
            'game_address': game_address,
        }
        client1, client2 = await self.search_single_game_clients(player1_id, player2_id)
        if not client1 or not client2:
            print("Error: Could not find both clients.")
            return
        new_game = SingleGame(game_id, player1_id, client1, player2_id, client2, game_address)
        print("New game created.", new_game.player1, new_game.player2, new_game.game_address)
        self.single_games.append(new_game)
        
        await send_message_to_client(player1_id, message)
        await send_message_to_client(player2_id, message)

    # Requests via game_service a new (keyboard)game address and sends it to the player
    async def create_keyboard_game(self, player1_id):
        print(f'Creating keyboard game for Player {player1_id}.')
        global game_id_counter
        game_id = game_id_counter
        game_id_counter += 1
        result = await sync_to_async(matchmaker_service.game_service.create_game)(game_id, player1_id, -1)
        game_address = result['game_address']
        message = {
            'action': 'game_address',
            'message': f'Keyboard Game successfully created. Join via: ',
            'game_address': game_address,
        }
        await send_message_to_client(player1_id, message)

    # Sends updated match information to the clients and starts the next match
    async def start_next_match(self, tournament):
        message = {
            'action': 'tournament_updated',
            'message': f'Tournament {tournament.id} has ended.',
            'tournament_id': tournament.id,
            'tournament': tournament.to_dict()
        }
        for player in tournament.players:
            await send_message_to_client(player, message)
        next_match = tournament.matches[tournament.current_match_index]
        await self.start_tournament_match(next_match['id'], next_match['players'][0], next_match['players'][1])

    # Processes the result of a single game and updates the user stats and game history
    async def process_single_game_result(self, game, winner, p1_wins, p2_wins): 
        general_points_for_winning = 5
        game.end_game(winner, p1_wins, p2_wins)

        # Player1, add game result to user stats
        is_winner = 1 if game.player1 == winner else 0
        print(f"p1: {game.player1}, p2: {game.player2}, winner: {winner}", 'gam.winner: ', game.game_winner, 'is_winner: ', is_winner)
        score = general_points_for_winning + abs(p1_wins - p2_wins) if is_winner else 0
        await sync_to_async(self.db.game_result_to_user_stats)(game.player1, is_winner, p1_wins, score)

        #Player2, add game result to user stats
        is_winner = 1 if game.player2 == winner else 0
        print(f"p1: {game.player1}, p2: {game.player2}, winner: {winner}", 'gam.winner: ', game.game_winner, 'is_winner: ', is_winner)
        score = general_points_for_winning + abs(p1_wins - p2_wins) if is_winner else 0
        await sync_to_async(self.db.game_result_to_user_stats)(game.player2, is_winner, p2_wins, score)

        # Add game to game history
        await sync_to_async(self.db.add_game)(game.player1, game.player2, winner, p1_wins, p2_wins)


    # Updates the result of a tournament match and starts the next match if there are any left or ends the tournament and sends the results to all players
    async def process_tournament_match_result(self, tournament, match, winner, p1_wins, p2_wins):
        match_index = tournament.matches.index(match)
        tournament.update_match_result(match_index, winner, p1_wins, p2_wins)
        if tournament.current_match_index < len(tournament.matches):
            await self.start_next_match(tournament)
        else:
            if tournament.end_tournament():
                message = {
                    'action': 'tournament_ended',
                    'message': f'Tournament {tournament.id} has ended.',
                    'tournament_id': tournament.id,
                    'tournament': tournament.to_dict()
                }
                for player in tournament.players:
                    await send_message_to_client(player, message)
                # As the tournament has ended, delete it from the database
                await sync_to_async(self.db.delete_tournament)(tournament.id)
                print(f"Tournament {tournament.id} has ended. Winner: {tournament.winner}")
            else:
                #Draw matches
                self.start_next_match(tournament)

    # Checks if game is a single game or a tournament match and processes the result accordingly
    async def process_game_result(self, game_id, winner, p1_wins, p2_wins):
        for game in self.single_games:
            if game.game_id == game_id:
                await self.process_single_game_result(game, winner, p1_wins, p2_wins)
                self.single_games.remove(game)
                return
            
        for tournament in self.tournaments:
            for match in tournament.matches:
                if match['id'] == game_id:
                    await self.process_tournament_match_result(tournament, match, winner, p1_wins, p2_wins)
                    return
        
        print(f"Game ID {game_id} not found.")
        return
    
    # If game_service sends -1 as winner, the game is aborted and gets removed
    async def abort_game(self, game_id):
        game = None
        for game in self.single_games:
            if game.game_id == game_id:
                game = game
                break
        if game is not None:
            game.abort_game()
            self.single_games.remove(game)
        else:
            print(f"Game ID {game_id} not found.")
        return
        
# MatchmakerService class for RPC to call methods externally from the game_service
class MatchmakerService:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        protocol = JSONRPCProtocol()

        transport_game = RabbitMQClientTransport(self.connection, 'game_service')
        self.game_service = RPCClient(protocol, transport_game).get_proxy()


    @public
    async def transmit_game_result(self, game_id, winner, p1_wins, p2_wins):
        print(f'Updating game result for Game ID: {game_id}, Winner: {winner}, P1 Wins: {p1_wins}, P2 Wins: {p2_wins}')
        if winner == -1:
            await matchmaker.abort_game(game_id)
            return
        await matchmaker.process_game_result(game_id, winner, p1_wins, p2_wins)


# Global variables
connected_clients = {}
game_id_counter = 0

dispatcher = RPCDispatcher()
matchmaker = MatchMaker()
matchmaker_service = MatchmakerService()
dispatcher.register_instance(matchmaker_service)

# Websocket handler gets called when a new connection is made or a message is received
async def handler(websocket, path):
    try:
        first_message = await websocket.recv()  # First message from client
        data = json.loads(first_message)
        action = data.get('action')
        client_id = int(data.get('player_id'))
        
        if action == 'handshake' and client_id:
            if connected_clients.get(client_id):
                print(f"Client {client_id} already connected.")
                await websocket.close()
                return
            client = Client(client_id, websocket)
            connected_clients[client_id] = client
            try:
                await consume_messages(websocket, client_id)
            finally:
                del connected_clients[client_id]
                await websocket.close()
        else:
            print("Error: First message did not contain a valid player_id")
            await websocket.close()
    except Exception as e:
        print(f"Error in handler: {e}")

# Consume messages from the client
async def consume_messages(websocket, client_id):
    async for message in websocket:
        try:
            data = json.loads(message)
            print(f"Received message from client {client_id}: {data}")
            if data.get('action') == 'request_single_game':
                player_id = int(data.get('player_id'))
                print(f"Requesting single game for player {player_id}.")
                await matchmaker.request_single_game(player_id) 
            elif data.get('action') == 'request_keyboard_game':
                player_id = int(data.get('player_id'))
                print(f"Requesting keyboard game for player {player_id}.")
                await matchmaker.request_keyboard_game(player_id)
            elif data.get('action') == 'request_tournament':
                player_id = int(data.get('player_id'))
                tournament_name = data.get('tournament_name')
                number_of_players = int(data.get('number_of_players'))
                print(f"Requesting tournament for player {player_id}.")
                await matchmaker.create_tournament(player_id, tournament_name, number_of_players)
            elif data.get('action') == 'join_tournament':
                player_id = int(data.get('player_id'))
                tournament_id = data.get('tournament_id')
                print(f"Joining tournament {tournament_id} for player {player_id}.")
                await matchmaker.join_tournament(player_id, tournament_id)      
            elif data.get('action') == 'game_address':
                print(f"Game address received: {data}")
        except ConnectionClosed:
            print(f"Connection with client {client_id} is closed.")
        except Exception as e:
            print(f"Error in consume_messages: {e}. Message: {message}")

# Send a message to a client
async def send_message_to_client(client_id, message):
    client = connected_clients.get(client_id)
    if client and client.websocket.open:
        try:
            await client.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending message to client {client_id}: {e}")
    else:
        print(f"Client {client_id} is not connected")

# Start the websocket server
async def start_websocket_server():
    async with websockets.serve(handler, "10.12.7.1", 8765):
        print("WebSocket server started on ws://10.12.7.1:8765")
        await asyncio.Future()

# Start the RPC server
async def run_servers():
    async with AioRPC('localhost', 'matchmaker_service_queue', MatchmakerService()):
        # Do anything else here
        await Future()


async def main():
    try:
        task1 = asyncio.create_task(start_websocket_server())
        task2 = asyncio.create_task(run_servers())
        await asyncio.gather(task1, task2)
    except asyncio.CancelledError:
        print("Main task cancelled.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Application interrupted. Exiting...")