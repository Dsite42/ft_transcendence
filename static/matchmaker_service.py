import pika
from tinyrpc.server import RPCServer
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.dispatch import public, RPCDispatcher
from tinyrpc.transports.rabbitmq import RabbitMQServerTransport
from tinyrpc import RPCClient
from tinyrpc.transports.rabbitmq import RabbitMQClientTransport

dispatcher = RPCDispatcher()

import django
from django.conf import settings
from django.db import models, connections
import json

class Database:
    def __init__(self, engine='django.db.backends.sqlite3', name=None, user=None, password=None, host=None, port=None):
        self.Model = None

        # Define the DATABASES dictionary
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

        # Update the settings with the custom DATABASES dictionary
        settings.configure(DATABASES=databases)

        # Initialize Django
        django.setup()

        # Create the custom base model
        class CustomBaseModel(models.Model):
            class Meta:
                app_label = 'frontapp'
                abstract = True

        self.Model = CustomBaseModel

    # Create a table if it doesnt exist
    def create_table(self, model):
        with connections['default'].schema_editor() as schema_editor:
            if model._meta.db_table not in connections['default'].introspection.table_names():
                schema_editor.create_model(model)

    # Update table if you added fields (doesn't drop fields as far as i know, which i was too afraid to implement)
    def update_table(self, model):
        with connections['default'].schema_editor() as schema_editor:
            # Check if the table exists
            if model._meta.db_table in connections['default'].introspection.table_names():
                # Get the current columns in the table
                current_columns = [field.column for field in model._meta.fields]

                # Get the database columns
                database_columns = connections['default'].introspection.get_table_description(connections['default'].cursor(), model._meta.db_table)
                database_column_names = [column.name for column in database_columns]

                # Check if each field in the model exists in the database table
                for field in model._meta.fields:
                    if field.column not in database_column_names:
                        # Add the new column to the table
                        schema_editor.add_field(model, field)

    def game_result_to_user_stats(self, game_id, winner, winner_diff_points):

        # Get the current stats for the user
        sql_query = "SELECT stats FROM auth_user WHERE username = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [winner])
            stats = cursor.fetchone()[0]

        # Deserialize the stats
        stats = json.loads(stats)

        # Update the 'games_won' field
        stats['games_won'] = stats.get('games_won', 0) + winner_diff_points

        # Serialize the stats
        stats = json.dumps(stats)

        # Update the stats in the database
        sql_query = "UPDATE auth_user SET stats = %s WHERE username = %s;"
        with connections['default'].cursor() as cursor:
            cursor.execute(sql_query, [stats, winner])













class MatchmakerService:
    def __init__(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        protocol = JSONRPCProtocol()

        # Transport for django_service_queue
        transport_django = RabbitMQClientTransport(connection, 'django_service_queue')
        self.django_service = RPCClient(protocol, transport_django).get_proxy()

        # Transport for game_service_queue
        transport_game = RabbitMQClientTransport(connection, 'game_service_queue')
        self.game_service = RPCClient(protocol, transport_game).get_proxy()

        self.db = Database(engine='django.db.backends.sqlite3', name='/home/cgodecke/Desktop/Core/ft_transcendence/frontend_draft/db.sqlite3')




    @public
    def update_game_result(self, game_id, winner, winner_diff_points):
        print(f'Updating game result for Game ID: {game_id}, Winner: {winner}, Winner Diff Points: {winner_diff_points}')
        self.db.game_result_to_user_stats(game_id, winner, winner_diff_points)
        return {"status": "success update_game_result"}

    @public
    def create_single_game(self, player1_id, player2_id):
        print(f'Creating single game between Player {player1_id} and Player {player2_id}')
        game_id = 1  # Beispiel-Spiel-ID
        self.game_service.start_game(player1_id, player2_id)
        return {"game_id": game_id, "status": "created"}

dispatcher.register_instance(MatchmakerService())

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
transport = RabbitMQServerTransport(connection, 'matchmaker_service_queue')

rpc_server = RPCServer(
    transport,
    JSONRPCProtocol(),
    dispatcher
)

print("Matchmaker Service RPC Server started...")
rpc_server.serve_forever()
