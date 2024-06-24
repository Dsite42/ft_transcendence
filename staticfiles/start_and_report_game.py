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

#example_transport = RabbitMQClientTransport(connection, 'example_service')
#example_service = RPCClient(protocol, example_transport).get_proxy()



# Spiel starten
game_id = 1
player1_id = 'dnebatz'
player2_id = 'Klaus'
winner = player1_id
p1_wins = 11
p2_wins = 7


#response = example_service.ping()
#print(response)
# Ergebnis übermitteln
response = matchmaker_service.transmit_game_result(game_id, winner, p1_wins, p2_wins)
print(f"Result sent: {response}")
