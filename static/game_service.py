import pika
from tinyrpc.server import RPCServer
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.dispatch import public, RPCDispatcher
from tinyrpc.transports.rabbitmq import RabbitMQServerTransport
from tinyrpc import RPCClient
from tinyrpc.transports.rabbitmq import RabbitMQClientTransport

dispatcher = RPCDispatcher()

class GameService:
    def __init__(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        protocol = JSONRPCProtocol()

        transport = RabbitMQClientTransport(connection, 'matchmaker_service_queue')
        self.matchmaker_service = RPCClient(protocol, transport).get_proxy()

    @public
    def start_game(self, player1_id):
        print(f'Starting game between Player {player1_id}')
        # Spiel-Logik simulieren
        result = {"game_id": 1, "winner": player1_id, "p1_wins": 10, "p2_wins": 4}
        print(f'Game result: {result}')
        return result

    @public
    def send_result(self, game_id, winner):
        print(f'Sending result for Game ID: {game_id}, Winner: {winner}')
        # Ergebnis an Matchmaker-Service senden
        return self.matchmaker_service.update_game_result(game_id, winner)

# Methoden registrieren
dispatcher.register_instance(GameService())

# Verbindung zu RabbitMQ herstellen
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
transport = RabbitMQServerTransport(connection, 'game_service_queue')

# RPC-Server einrichten
rpc_server = RPCServer(
    transport,
    JSONRPCProtocol(),
    dispatcher
)

print("Game Service RPC Server started...")
rpc_server.serve_forever()
