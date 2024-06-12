import pika
from tinyrpc.server import RPCServer
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.dispatch import public, RPCDispatcher
from tinyrpc.transports.rabbitmq import RabbitMQServerTransport
from tinyrpc import RPCClient
from tinyrpc.transports.rabbitmq import RabbitMQClientTransport

import asyncio
import websockets
import json
from concurrent.futures import ThreadPoolExecutor
import time

dispatcher = RPCDispatcher()

import django
from django.conf import settings
from django.db import models, connections

# Thread-sichere asyncio Warteschlange zur Kommunikation zwischen Threads
message_queue = asyncio.Queue()
global g_consumer_id

def set_consumer_id(consumer_id):
    global g_consumer_id
    g_consumer_id = consumer_id


async def handler(websocket, path):
    consumer_id = id(websocket)
    consumer_task = asyncio.create_task(consume_messages(websocket, consumer_id))
    producer_task = asyncio.create_task(produce_messages(websocket, consumer_id))

    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()

async def consume_messages(websocket, consumer_id):
    async for message in websocket:
        data = json.loads(message)
        print(f"Received message from client: {data}")
        if data.get('action') == 'start_game':
            set_consumer_id(consumer_id)
            player1_id = data.get('player1_id')
            player2_id = data.get('player2_id')
            await message_queue.put({
                'status': 'success',
                'message': f'Game is being created for {player1_id} and {player2_id}. consumer_id: {consumer_id}',
                'consumer_id': consumer_id
            })

async def produce_messages(websocket, consumer_id):
    while True:
        try:
            start_time = time.time()
            message = await asyncio.wait_for(message_queue.get(), timeout=1)
            if message is None:
                break
            if message.get('consumer_id') == consumer_id:
                await websocket.send(json.dumps(message))
            end_time = time.time()
            print(f"produce_messages loop took {end_time - start_time:.2f} seconds")
        except asyncio.TimeoutError:
            continue
        except Exception as e:
            print(f"Error in produce_messages: {e}")

            
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

    def game_result_to_user_stats(self, game_id, winner, winner_diff_points):
        sql_query = "SELECT stats FROM auth_user WHERE username = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [winner])
            stats = cursor.fetchone()[0]

        stats = json.loads(stats)
        stats['games_won'] = stats.get('games_won', 0) + winner_diff_points
        stats = json.dumps(stats)

        sql_query = "UPDATE auth_user SET stats = %s WHERE username = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [stats, winner])

class MatchmakerService:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        protocol = JSONRPCProtocol()

        transport_django = RabbitMQClientTransport(self.connection, 'django_service_queue')
        self.django_service = RPCClient(protocol, transport_django).get_proxy()

        transport_game = RabbitMQClientTransport(self.connection, 'game_service_queue')
        self.game_service = RPCClient(protocol, transport_game).get_proxy()

        self.db = Database(engine='django.db.backends.sqlite3', name='/home/cgodecke/Desktop/Core/ft_transcendence/frontend_draft/db.sqlite3')

    @public
    def update_game_result(self, game_id, winner, winner_diff_points):
        print(f'Updating game result for Game ID: {game_id}, Winner: {winner}, Winner Diff Points: {winner_diff_points}')
        self.db.game_result_to_user_stats(game_id, winner, winner_diff_points)
        return {"status": "success update_game_result"}

    @public
    def create_single_game(self, player1_id, player2_id):
        start_time = time.time()
        print(f'Creating single game between Player {player1_id} and Player {player2_id}. consumer_id: {g_consumer_id}')
        game_id = 1
        result = self.game_service.start_game(player1_id, player2_id)
        self.update_game_result(result['game_id'], result['winner'], result['winner_diff_points'])
        message = {
            'status': 'success',
            'message': f'Game successfully created. Join via abc.com:1234',
            'consumer_id': g_consumer_id  # Hier wird die consumer_id hinzugefügt
        }
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(message_queue.put(message))
        loop.close()
        end_time = time.time()
        print(f"create_single_game took {end_time - start_time:.2f} seconds")
        return {"game_id": game_id, "status": "created"}

dispatcher.register_instance(MatchmakerService())

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

async def main():
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor()
    loop.run_in_executor(executor, start_rpc_server)

    await start_websocket_server()

if __name__ == "__main__":
    asyncio.run(main())
