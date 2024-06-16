import asyncio
import signal
import json
import time
from concurrent.futures import ThreadPoolExecutor
import threading

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
from asgiref.sync import sync_to_async

#define classes
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


    def game_result_to_user_stats(self, game_id, winner, p1_wins, p2_wins):
        sql_query = "SELECT stats FROM auth_user WHERE username = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [winner])
            stats = cursor.fetchone()[0]

        stats = json.loads(stats)
        general_points_for_winning = 5
        stats['games_won'] = stats.get('games_won', 0) + general_points_for_winning + (p1_wins - p2_wins)
        stats = json.dumps(stats)

        sql_query = "UPDATE auth_user SET stats = %s WHERE username = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [stats, winner])
            
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
    
    def create_single_game(self, player_id):
        start_time = time.time()
        print(f'Creating single game between Player {player_id}. consumer_id: {g_consumer_id}')
        game_id = 1
        result = matchmaker_service.game_service.start_game(player_id)
        matchmaker_service.update_game_result(result['game_id'], result['winner'], result['p1_wins'], result['p2_wins'])
        message = {
            'status': 'success',
            'message': f'Game successfully created. Join via abc.com:1234',
            'consumer_id': g_consumer_id
        }
        message_queue.put_nowait(message)
        message_queue._loop._write_to_self()
        
        end_time = time.time()
        print(f"create_single_game took {end_time - start_time:.2f} seconds")
        return {"game_id": game_id, "status": "created"}



class MatchmakerService:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        protocol = JSONRPCProtocol()

        transport_django = RabbitMQClientTransport(self.connection, 'django_service_queue')
        self.django_service = RPCClient(protocol, transport_django).get_proxy()

        transport_game = RabbitMQClientTransport(self.connection, 'game_service_queue')
        self.game_service = RPCClient(protocol, transport_game).get_proxy()

        self.db = Database(engine='django.db.backends.sqlite3', name='/home/chris/Core/ft_transcendence/frontend_draft/db.sqlite3')

    @public
    def update_game_result(self, game_id, winner, p1_wins, p2_wins):
        print(f'Updating game result for Game ID: {game_id}, Winner: {winner}, P1 Wins: {p1_wins}, P2 Wins: {p2_wins}')
        
        self.db.game_result_to_user_stats(game_id, winner, p1_wins, p2_wins)
        return {"status": "success update_game_result"}

    #@public
    #def create_single_game(self, player1_id):
    #    start_time = time.time()
    #    print(f'Creating single game between Player {player1_id}. consumer_id: {g_consumer_id}')
    #    game_id = 1
    #    result = self.game_service.start_game(player1_id)
    #    self.update_game_result(result['game_id'], result['winner'], result['p1_wins'], result['p2_wins'])
    #    message = {
    #        'status': 'success',
    #        'message': f'Game successfully created. Join via abc.com:1234',
    #        'consumer_id': g_consumer_id
    #    }
    #    message_queue.put_nowait(message)
    #    message_queue._loop._write_to_self()
    #    
    #    end_time = time.time()
    #    print(f"create_single_game took {end_time - start_time:.2f} seconds")
    #    return {"game_id": game_id, "status": "created"}






dispatcher = RPCDispatcher()
matchmaker = matchMaker()
matchmaker_service = MatchmakerService()
dispatcher.register_instance(matchmaker_service)
global g_consumer_id
# Thread-safe asyncio queue for communication between threads
message_queue = asyncio.Queue()






def set_consumer_id(consumer_id):
    global g_consumer_id
    g_consumer_id = consumer_id

async def handler(websocket, path):
    consumer_id = id(websocket)
    async with asyncio.TaskGroup() as tg:
        consumer_task = tg.create_task(consume_messages(websocket, consumer_id))
        producer_task = tg.create_task(produce_messages(websocket, consumer_id))

async def consume_messages(websocket, consumer_id):
    async for message in websocket:
        try:
            data = json.loads(message)
            print(f"Received message from client: {data}")
            if data.get('action') == 'start_single_game':
                set_consumer_id(consumer_id)
                player_id = data.get('player_id')
                
                #create_single_game(player_id)
                # Use sync_to_async to call the synchronous function
                await sync_to_async(matchmaker.create_single_game)(player_id)                
                #await message_queue.put({
                #    'status': 'success',
                #    'message': f'Game is being created for {player1_id}. consumer_id: {consumer_id}',
                #    'consumer_id': consumer_id
                #})
        except Exception as e:
            print(f"Error in consume_messages: {e}")

async def produce_messages(websocket, consumer_id):
    try:
        while True:
            start_time = time.time()
            message = await message_queue.get()
            if message is None:
                break
            if message.get('consumer_id') == consumer_id:
                await websocket.send(json.dumps(message))
            end_time = time.time()
            print(f"produce_messages loop took {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"Error in produce_messages: {e}")












def start_rpc_server():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    transport = RabbitMQServerTransport(connection, 'matchmaker_service_queue')

    rpc_server = RPCServer(
        transport,
        JSONRPCProtocol(),
        dispatcher
    )

    print("Matchmaker Service RPC Server started...")
    rpc_server.serve_forever()

async def start_websocket_server():
    async with websockets.serve(handler, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()

async def run_servers():
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor()
    rpc_server_thread = threading.Thread(target=start_rpc_server, daemon=True)
    rpc_server_thread.start()
    await start_websocket_server()

async def handle_shutdown(loop, executor):
    print("Shutting down...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    await loop.shutdown_asyncgens()
    executor.shutdown(wait=False)
    print("Shutdown complete.")

async def main():
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(handle_shutdown(loop, executor)))

    try:
        await run_servers()
    except asyncio.CancelledError:
        print("Main task cancelled.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Application interrupted. Exiting...")
