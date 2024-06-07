import pika
from tinyrpc.server import RPCServer
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.dispatch import public, RPCDispatcher
from tinyrpc.transports.rabbitmq import RabbitMQServerTransport
from django.core.management.base import BaseCommand

dispatcher = RPCDispatcher()

class DjangoService:
    @public
    def notify_game_created(self, game_id, player1_id, player2_id):
        print(f'Game created: Game ID: {game_id}, Player1: {player1_id}, Player2: {player2_id}')
        # Hier können Sie die Logik zum Verarbeiten der Spielbenachrichtigung hinzufügen
        return {"status": "notified"}
    

dispatcher.register_instance(DjangoService())

class Command(BaseCommand):
    help = 'Starts the RPC server for Django'

    def handle(self, *args, **kwargs):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        transport = RabbitMQServerTransport(connection, 'django_service_queue')
        rpc_server = RPCServer(
            transport,
            JSONRPCProtocol(),
            dispatcher
        )

        print("Starting Django RPC Server...")
        rpc_server.serve_forever()
