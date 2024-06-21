#!/usr/bin/env python3

# create_game.py: Requests the game service to start a new game
# This script is meant for authorization testing and won't be used during normal runtime

from sys import stderr
from tinyrpc.client import RPCClient
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.rabbitmq import RabbitMQClientTransport
from argparse import ArgumentParser, Namespace
from pika import BlockingConnection, ConnectionParameters

def parse_arguments() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        '-r', '--rpc-host',
        type=str, required=True,
        help="host of the RPC message broker"
    )
    parser.add_argument(
        '-i', '--game-id',
        type=int, required=True,
        help="database ID of the game"
    )
    parser.add_argument(
        '-I', '--player-ids',
        type=int, nargs=2, required=True,
        help="user IDs (2) that are considered as players (must be unique, -1 for guest)"
    )
    arguments = parser.parse_args()
    # Check if the given player IDs are valid
    if len(set(arguments.player_ids)) != 2:
        parser.error('player IDs must be unique')
    for player_id in arguments.player_ids:
        if player_id < 0 and player_id != -1:
            parser.error('player IDs must be positive or -1 for guest')
    return arguments

if __name__ == '__main__':
    try:
        arguments = parse_arguments()
        # Connect to RabbitMQ and get the game service proxy
        game_service = RPCClient(
            JSONRPCProtocol(),
            RabbitMQClientTransport(
                BlockingConnection(
                    ConnectionParameters(arguments.rpc_host)
                ),
                'game_service'
            )
        ).get_proxy()
        # Call the `create_game` method on the game service
        result = game_service.create_game(arguments.game_id, *arguments.player_ids)
        if result == None or not 'game_address' in result:
            print('fatal: Game service was unable to create game', file=stderr)
            exit(1)
        print(f'Created new game at: {result["game_address"]}')
    except KeyboardInterrupt:
        pass
