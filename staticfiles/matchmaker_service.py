import asyncio
import asyncstdlib as astd
import signal
import json
import time

import django
from django.conf import settings
from django.db import models, connections

import pika
from tinyrpc.server import RPCServer
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.dispatch import public, RPCDispatcher
from tinyrpc.transports.rabbitmq import RabbitMQServerTransport, RabbitMQClientTransport
from tinyrpc import RPCClient

import websockets
from websockets.exceptions import ConnectionClosed
from asgiref.sync import sync_to_async
from datetime import datetime

from aiorpc import AioRPC
from asyncio import Future, sleep, run

#define classes

class Client:
    def __init__(self, player_id, websocket):
        self.player_id = player_id
        self.websocket = websocket
        
class Tournament:
    def __init__(self, tournament_id, creator, tournament_name, number_of_players):
        self.id = tournament_id
        self.creator = creator
        self.name = tournament_name
        self.number_of_players = number_of_players
        self.start_time = datetime.now()
        self.end_time = None
        self.players = []
        self.status = 'waiting'
        self.winner = None

    def join_tournament(self, player):
        if len(self.players) == self.number_of_players:
            return False
        self.players.append(player)

    def start_tournament(self):
        self.status = 'started'

    def abort_tournament(self):
        self.winner = None
        self.status = 'aborted'

    def end_tournament(self, winner):
        self.end_time = datetime.now()
        self.status = 'ended'
        self.winner = winner


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


''' from the django-db standalone github
    def create_table(self, model):
        with connections['default'].schema_editor() as schema_editor:
            if model._meta.db_table not in connections['default'].introspection.table_names():
                schema_editor.create_model(model)

    def update_table(self, model):
        with connections['default'].schema_editor() as schema_editor:
            if model._meta.db_table in connections['default'].introspection.table_names():
                current_columns = [field.column for field in model._meta.fields]
                database_columns = connections['default'].introspection.get_table_description(connections['default'].cursor(), model._meta.db_table)
                database_column_names = [column.name for column in database_columns]

                for field in model._meta.fields:
                    if field.column not in database_column_names:
                        schema_editor.add_field(model, field)
'''


        
    
class MatchMaker:
    def __init__(self):
        self.db = Database(engine='django.db.backends.sqlite3', name='/home/cgodecke/Desktop/Core/ft_transcendence/frontend_draft/db.sqlite3')
        self.game_id_counter = 0
        self.tournaments = []
        self.single_games = []
        self.single_games_queue = []


    async def create_tournament(self, creator, tournament_name, number_of_players):
        new_tournament = Tournament(0, creator, tournament_name, number_of_players)
        new_tournament.id = await sync_to_async(self.db.add_tournament)(new_tournament)
        self.tournaments.append(new_tournament)
        message = {
            'action': 'tournement_created',
            'message': f'Tournement successfully created. ID: ',
            'tournement_id': new_tournament.id,
        }
        await send_message_to_client(creator, message)

        print(f"Tournament created: id {new_tournament.id} name: {new_tournament.name}, creator: {new_tournament.creator}, size: {new_tournament.number_of_players}")
    
    async def request_single_game(self, player1):
        self.single_games_queue.append(player1)
        await self.check_single_game_queue()

    async def request_keyboard_game(self, player1):
        await self.create_keyboard_game(player1)
                
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
        
    
    async def create_single_game(self, player1_id, player2_id):
        start_time = time.time()
        print(f'Creating single game between Player {player1_id} and Player {player2_id}.')
        game_id = self.game_id_counter
        self.game_id_counter += 1
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
        
        # Send message to both players
        await send_message_to_client(player1_id, message)
        await send_message_to_client(player2_id, message)
        
        end_time = time.time()
        print(f"create_single_game took {end_time - start_time:.2f} seconds")
    
    async def create_keyboard_game(self, player1_id):
        print(f'Creating keyboard game for Player {player1_id}.')
        game_id = self.game_id_counter
        self.game_id_counter += 1
        result = await sync_to_async(matchmaker_service.game_service.create_game)(game_id, player1_id, -1)
        game_address = result['game_address']
        message = {
            'action': 'game_address',
            'message': f'Keyboard Game successfully created. Join via: ',
            'game_address': game_address,
        }
        await send_message_to_client(player1_id, message)

        
    async def process_game_result(self, game_id, winner, p1_wins, p2_wins):
        game = None
        for game in self.single_games:
            if game.game_id == game_id:
                game = game
                break
        general_points_for_winning = 5
        if game is not None:
            game.end_game(winner, p1_wins, p2_wins)
            # Player1
            is_winner = 1 if game.player1 == winner else 0
            print(f"p1: {game.player1}, p2: {game.player2}, winner: {winner}", 'gam.winner: ', game.game_winner, 'is_winner: ', is_winner)
            score = general_points_for_winning + abs(p1_wins - p2_wins) if is_winner else 0
            await sync_to_async(self.db.game_result_to_user_stats)(game.player1, is_winner, p1_wins, score)
            #Player2
            is_winner = 1 if game.player2 == winner else 0
            print(f"p1: {game.player1}, p2: {game.player2}, winner: {winner}", 'gam.winner: ', game.game_winner, 'is_winner: ', is_winner)
            score = general_points_for_winning + abs(p1_wins - p2_wins) if is_winner else 0
            await sync_to_async(self.db.game_result_to_user_stats)(game.player2, is_winner, p2_wins, score)

            await sync_to_async(self.db.add_game)(game.player1, game.player2, winner, p1_wins, p2_wins)
        else:
            print(f"Game ID {game_id} not found.")
        return
    
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
        

class MatchmakerService:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        protocol = JSONRPCProtocol()

        transport_django = RabbitMQClientTransport(self.connection, 'django_service_queue')
        self.django_service = RPCClient(protocol, transport_django).get_proxy()

        transport_game = RabbitMQClientTransport(self.connection, 'game_service')
        self.game_service = RPCClient(protocol, transport_game).get_proxy()



    @public
    async def transmit_game_result(self, game_id, winner, p1_wins, p2_wins):
        print(f'Updating game result for Game ID: {game_id}, Winner: {winner}, P1 Wins: {p1_wins}, P2 Wins: {p2_wins}')
        if winner == -1:
            await matchmaker.abort_game(game_id)
            return
        print("Type:" , type(winner))
        await matchmaker.process_game_result(game_id, winner, p1_wins, p2_wins)


dispatcher = RPCDispatcher()
matchmaker = MatchMaker()
matchmaker_service = MatchmakerService()
dispatcher.register_instance(matchmaker_service)
connected_clients = {}

class ExampleService:
    @public
    def ping(self) -> str:
        return 'Pong!'

    @public
    async def ping_with_delay(self) -> str:
        await sleep(5.0)
        return 'Pong! (with delay :D)'


async def handler(websocket, path):
    try:
        first_message = await websocket.recv()  # Erste Nachricht vom Client
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
            elif data.get('action') == 'join_tournement':
                player_id = int(data.get('player_id'))
                tournament_id = int(data.get('tournament_id'))
                print(f"Joining tournament {tournament_id} for player {player_id}.")
                await matchmaker.join_tournament(player_id, tournament_id)      
            elif data.get('action') == 'game_address':
                print(f"Game address received: {data}")
        except ConnectionClosed:
            print(f"Connection with client {client_id} is closed.")
        except Exception as e:
            print(f"Error in consume_messages: {e}")

async def send_message_to_client(client_id, message):
    client = connected_clients.get(client_id)
    print("Type send_message_to_client:", type(client_id), "client:", client)
    if client and client.websocket.open:
        try:
            await client.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending message to client {client_id}: {e}")
    else:
        print(f"Client {client_id} is not connected")


async def start_websocket_server():
    async with websockets.serve(handler, "10.12.6.1", 8765):
        print("WebSocket server started on ws://10.12.6.1:8765")
        await asyncio.Future()

async def run_servers():
    async with AioRPC('localhost', 'matchmaker_service_queue', MatchmakerService()):
        # Do anything else here
        await Future()

async def handle_shutdown(loop, executor):
    print("Shutting down...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    await loop.shutdown_asyncgens()
    executor.shutdown(wait=False)
    print("Shutdown complete.")

async def main():
    #await matchmaker.process_game_result(7, 4, 11, 8)
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