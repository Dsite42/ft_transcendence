import asyncio
from asyncio import Future, sleep
import json
import os
import time
from sys import stderr


from .aiorpc import AioRPC
import pika
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.dispatch import public, RPCDispatcher
from tinyrpc.transports.rabbitmq import RabbitMQClientTransport
from tinyrpc import RPCClient

import websockets
from websockets.exceptions import ConnectionClosed
from asgiref.sync import sync_to_async
from datetime import datetime
from jwt import decode as jwt_decode
from typing import Optional, Tuple


from itertools import combinations
from .websocket_client import WebsocketClient
from .game_types import SingleGame, Tournament
from .database import Database
from . import my_global_vars

# Class definitions


# Client class for handling clients
class Client:
    def __init__(self, player_id, websocket):
        self.player_id = player_id
        self.websocket = websocket

# The MatchMaker class handles the matchmaking process for keyboard games, single games and tournaments. It is the main service that communicates with the game_service and the clients.    
class MatchMaker:
    def __init__(self):
        self.db_path = os.path.join(os.getcwd(), 'db.sqlite3')
        self.db = Database(engine='django.db.backends.sqlite3', name=self.db_path)
        print("db_path1: ", self.db_path)
        self.db.delete_all_tournaments()
        self.tournaments = []
        self.single_games = []
        self.single_games_queue = []
        self.keyboard_games = []

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
            await self.start_tournament_match(tournament, tournament.matches[0]['id'], tournament.matches[0]['players'][0], tournament.matches[0]['players'][1])

    # Requests via game_service a new tournament match and sends the game address to the players
    async def start_tournament_match(self, tournament, game_id, player1_id, player2_id):
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
            self.abort_tournament(tournament)
            return
        
        await send_message_to_client(player1_id, message)
        await send_message_to_client(player2_id, message)
        
    # Adds a player to a tournament and checks if the tournament is full
    async def join_tournament(self, player_id, tournament_id):
        if await self.is_client_already_playing(player_id):
            return
        tournament = None
        for t in self.tournaments:
            if t.id == tournament_id:
                tournament = t
                break
        if tournament is not None:
            join_tournament_result = tournament.join_tournament(player_id)
            print(f"Join tournament result: {join_tournament_result}")
            match join_tournament_result:
                # Player successfully joined the tournament
                case 1: 
                    tournament.display_names[player_id] = await sync_to_async(self.db.get_display_name)(player_id)
                    message = {
                        'action': 'tournament_joined',
                        'message': f'Player {tournament.display_names[player_id]} successfully joined tournament {tournament_id}.',
                        'tournament_id': tournament.id,
                        'tournament': tournament.to_dict()
                    }
                    await sync_to_async(self.db.add_player_to_tournament)(tournament_id, player_id)
                    if len(tournament.players) < tournament.number_of_players:
                        for player in tournament.players:
                            await send_message_to_client(player, message)
                    print(f"Player {player_id} joined tournament {tournament_id}.")
                    await self.check_tournament_readyness(tournament)
                # Tournament is full
                case 0:
                    message = {
                        'action': 'tournament_full',
                        'message': f'Tournament {tournament_id} is full.',
                    }
                    await send_message_to_client(player_id, message)
                    print(f"Tournament {tournament_id} is full.")
                # Player is already in the tournament
                case -1:
                    print(f"Player {player_id} is already in tournament {tournament_id}.")
                    message = {
                        'action': 'already_in_tournament',
                        'message': f'Player {player_id} is already in tournament {tournament_id}.',
                        'tournament': tournament.to_dict()
                    }
                    await send_message_to_client(player_id, message)
        
        else:
            message = {
                'action': 'tournament_not_found',
                'message': f'Tournament {tournament_id} not found.',
            }
            await send_message_to_client(player_id, message)
            print(f"Tournament {tournament_id} not found.")

    # Adds a player to the single game queue and checks if there are enough players to start a game
    async def request_single_game(self, player1):
        if await self.is_client_already_playing(player1):
            return
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
        game_id = my_global_vars.game_id_counter
        my_global_vars.game_id_counter += 1
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
        if await self.is_client_already_playing(player1_id):
            return
        print(f'Creating keyboard game for Player {player1_id}.')
        game_id = my_global_vars.game_id_counter
        my_global_vars.game_id_counter += 1
        result = await sync_to_async(matchmaker_service.game_service.create_game)(game_id, player1_id, -1)
        game_address = result['game_address']
        message = {
            'action': 'game_address',
            'message': f'Keyboard Game successfully created. Join via: ',
            'game_address': game_address,
        }
        new_game = SingleGame(game_id, player1_id, connected_clients.get(player1_id), -1, None, game_address)
        self.keyboard_games.append(new_game)
        await send_message_to_client(player1_id, message)


    # Sends updated match information to the clients and starts the next match
    async def start_next_match(self, tournament):
        next_match = tournament.matches[tournament.current_match_index]

        # Check if players are still connected
        client1, client2 = await self.search_single_game_clients(next_match['players'][0], next_match['players'][1])
        if not client1 or not client2:
            print("Error: Could not find both clients.")
            await self.abort_tournament(tournament)
            return
        
        message = {
            'action': 'tournament_updated',
            'message': f'Tournament {tournament.id} results update.',
            'tournament_id': tournament.id,
            'tournament': tournament.to_dict()
        }
        for player in tournament.players:
            await send_message_to_client(player, message)
        try:
            await self.start_tournament_match(tournament, next_match['id'], next_match['players'][0], next_match['players'][1])
        except Exception as e:
            print(f"Error starting next match: {e}")

    # Processes the result of a single game and updates the user stats and game history
    async def process_single_game_result(self, game, winner, p1_wins, p2_wins): 
        general_points_for_winning = 5
        game.end_game(winner, p1_wins, p2_wins)

        # Player1, add game result to user stats
        is_winner = 1 if game.player1 == winner else 0
        print(f"p1: {game.player1}, p2: {game.player2}, winner: {winner}", 'gam.winner: ', game.game_winner, 'is_winner: ', is_winner)
        p1_score = general_points_for_winning + abs(p1_wins - p2_wins) if is_winner else 0
        await sync_to_async(self.db.game_result_to_user_stats)(game.player1, is_winner, p1_wins, p1_score)

        #Player2, add game result to user stats
        is_winner = 1 if game.player2 == winner else 0
        print(f"p1: {game.player1}, p2: {game.player2}, winner: {winner}", 'gam.winner: ', game.game_winner, 'is_winner: ', is_winner)
        p2_score = general_points_for_winning + abs(p1_wins - p2_wins) if is_winner else 0
        await sync_to_async(self.db.game_result_to_user_stats)(game.player2, is_winner, p2_wins, p2_score)

        # Add game to game history
        await sync_to_async(self.db.add_game)(game.player1, game.player2, winner, p1_wins, p2_wins)

        # Send game result to clients
        winner_name = await sync_to_async(self.db.get_display_name)(game.game_winner)
        message = {
            'action': 'single_game_ended',
            'message': f'Game {game.game_id} has ended.',
            'game_id': game.game_id,
            'winner': winner_name,
            'score': p1_score if game.player1 == game.game_winner else p2_score
        }
        await send_message_to_client(game.player1, message)
        await send_message_to_client(game.player2, message)


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
                self.tournaments.remove(tournament)
                print(f"Tournament {tournament.id} has ended. Winner: {tournament.winner}")
            else:
                #Draw matches
                self.start_next_match(tournament)

    # Checks if game is a single game or a tournament match and processes the result accordingly
    async def process_game_result(self, game_id, winner, p1_wins, p2_wins):
        for game in self.keyboard_games:
            if game.game_id == game_id:
                self.keyboard_games.remove(game)
                return

        for game in self.single_games:
            if game.game_id == game_id:
                if winner == -1:
                    await self.abort_single_game(game)
                    return
                else:
                    await self.process_single_game_result(game, winner, p1_wins, p2_wins)
                    self.single_games.remove(game)
                    return
            
        for tournament in self.tournaments:
            for match in tournament.matches:
                if match['id'] == game_id:
                    if winner == -1:
                        await self.abort_tournament(tournament)
                        return
                    else:
                        await self.process_tournament_match_result(tournament, match, winner, p1_wins, p2_wins)
                        return
        
        print(f"Game ID {game_id} not found.")
        return
    
    # If game_service sends -1 as winner, the game is aborted and gets removed
    async def abort_single_game(self, game):
        game.abort_game()
        self.single_games.remove(game)
        message = {
            'action': 'single_game_aborted',
            'message': f'Game {game.game_id} has been aborted.',
            'game_id': game.game_id,
        }
        await send_message_to_client(game.player1, message)
        await send_message_to_client(game.player2, message)

    async def abort_tournament(self, tournament):
        tournament.abort_tournament()
        message = {
            'action': 'tournament_aborted',
            'message': f'Tournament {tournament.id} has been aborted.',
            'tournament_id': tournament.id,
        }
        for player in tournament.players:
            await send_message_to_client(player, message)
        await sync_to_async(self.db.delete_tournament)(tournament.id)
        self.tournaments.remove(tournament)
        print(f"Tournament {tournament.id} has been aborted.")

    async def check_and_delete_player_from_waiting_tournament(self, player_id):
        for tournament in self.tournaments:
            if player_id in tournament.players and tournament.status == 'waiting':
                tournament.players.remove(player_id)
                await sync_to_async(self.db.delete_player_from_tournament)(tournament.id, player_id)
                message = {
                    'action': 'tournament_updated',
                    'message': f'Player {tournament.display_names[player_id]} has left tournament {tournament.id}.',
                    'tournament_id': tournament.id,
                    'tournament': tournament.to_dict()
                }
                for player in tournament.players:
                    await send_message_to_client(player, message)

    async def is_client_already_playing(self, player_id):
        is_already_playing = False

        for game in self.keyboard_games:
            if game.player1 == player_id:
                print(f"Player {player_id} is already playing a keyboard game.")
                is_already_playing = True
        for game in self.single_games:
            if game.player1 == player_id or game.player2 == player_id:
                print(f"Player {player_id} is already playing a single game.")
                is_already_playing = True
        for tournament in self.tournaments:
            if player_id in tournament.players:
                print(f"Player {player_id} is already in a tournament.")
                is_already_playing = True
 
        if is_already_playing:
            message = {
            'action': 'already_playing',
            'message': f'You are already playing a game.',
            }
            await send_message_to_client(player_id, message)

        return is_already_playing




        
# MatchmakerService class for RPC to call methods externally from the game_service
class MatchmakerService:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        protocol = JSONRPCProtocol()

        transport_game = RabbitMQClientTransport(self.connection, 'game_service')
        self.game_service = RPCClient(protocol, transport_game).get_proxy()


    @public
    async def transmit_game_result(self, game_id, winner, p1_wins, p2_wins):
        print(f'Updating game result for Game ID: {game_id}, Winner: {winner}, P1 Wins: {p1_wins}, P2 Wins: {p2_wins}', file=stderr)
        await matchmaker.process_game_result(game_id, winner, p1_wins, p2_wins)


# Global variables
connected_clients = {}
time.sleep(10)

dispatcher = RPCDispatcher()
matchmaker = MatchMaker()
matchmaker_service = MatchmakerService()
dispatcher.register_instance(matchmaker_service)
print("db_path: ", matchmaker.db_path)
print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXx")


# Websocket handler gets called on a new connection
async def handler(websocket):
    try:
        client_id = websocket.user_id
        client = Client(client_id, websocket)
        connected_clients[client_id] = client
        await consume_messages(websocket, client_id)
    except Exception as e:
        print(f"Error in handler: {e}")
    finally:
        del connected_clients[client_id]
        await matchmaker.check_and_delete_player_from_waiting_tournament(client_id)
        await websocket.close()

# Consume messages from the client
async def consume_messages(websocket, client_id):
    async for message in websocket:
        try:
            data = json.loads(message)
            print(f"Received message from client {client_id}: {data}")
            if data.get('action') == 'request_single_game':
                player_id = websocket.user_id
                print(f"Requesting single game for player {player_id}.")
                await matchmaker.request_single_game(player_id) 
            elif data.get('action') == 'request_keyboard_game':
                player_id = websocket.user_id
                print(f"Requesting keyboard game for player {player_id}.")
                await matchmaker.request_keyboard_game(player_id)
            elif data.get('action') == 'request_tournament':
                player_id = websocket.user_id
                tournament_name = data.get('tournament_name')
                number_of_players = int(data.get('number_of_players'))
                print(f"Requesting tournament for player {player_id}.")
                await matchmaker.create_tournament(player_id, tournament_name, number_of_players)
            elif data.get('action') == 'join_tournament':
                player_id = websocket.user_id
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

    async with websockets.serve(handler, os.getenv('GAME_HOST').strip(), 8765, create_protocol=WebsocketClient):
        game_host = os.getenv('GAME_HOST').strip()
        print(f"GAME_HOST: '{game_host}'")
        print("WebSocket server started on ws://", os.getenv('GAME_HOST').strip(), ":8765")

        await asyncio.Future()

# Start the RPC server
async def run_servers():
    async with AioRPC('rabbitmq', 'matchmaker_service_queue', MatchmakerService()):
        # Do anything else here
        await Future()

async def keep_connection_alive():
    while True:
        matchmaker_service.connection.process_data_events(time_limit=0.100)
        await sleep(20)

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(start_websocket_server())
            task2 = tg.create_task(run_servers())
            task3 = tg.create_task(keep_connection_alive())
    except asyncio.CancelledError:
        print("Main task cancelled.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Application interrupted. Exiting...")