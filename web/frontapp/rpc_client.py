import pika
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.rabbitmq import RabbitMQClientTransport
from tinyrpc import RPCClient

def get_matchmaker_service():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    transport = RabbitMQClientTransport(connection, 'matchmaker_service_queue')
    protocol = JSONRPCProtocol()
    rpc_client = RPCClient(protocol, transport)
    return rpc_client.get_proxy(), connection
