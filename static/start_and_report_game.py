import pika
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.rabbitmq import RabbitMQClientTransport
from tinyrpc import RPCClient

# Verbindung zu RabbitMQ herstellen
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
matchmaker_transport = RabbitMQClientTransport(connection, 'matchmaker_service_queue')
protocol = JSONRPCProtocol()

# RPC-Client einrichten
matchmaker_service = RPCClient(protocol, matchmaker_transport).get_proxy()

# Spiel starten
game_id = 1
player1_id = 'dnebatz'
player2_id = 'Klaus'
winner = player1_id
winner_diff_points = -4


# Ergebnis übermitteln
response = matchmaker_service.update_game_result(game_id, winner, winner_diff_points)
print(f"Result sent: {response}")
