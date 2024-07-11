from .service import GameService

import re
from sys import stderr
from asyncio import run
from argparse import ArgumentParser, Namespace

def parse_arguments() -> Namespace:
    parser = ArgumentParser(description='Manages game servers and provides an RPC interface')
    parser.add_argument(
        '-r', '--rpc-host',
        type=str, required=True,
        help="host of the RPC message broker"
    )
    parser.add_argument(
        '-g', '--game-host',
        type=str, required=True,
        help="host of the exposed game servers"
    )
    parser.add_argument(
        '-p', '--port-range',
        type=str, required=True,
        help="range of the exposed game server ports"
    )
    parser.add_argument(
        '-j', '--jwt-secret',
        type=str, required=True,
        help="the secret used to validate a JWT token's authenticity"
    )
    parser.add_argument(
        '-c', '--ssl-cert',
        type=str, default=None,
        help="the server's SSL certificate file"
    )
    parser.add_argument(
        '-k', '--ssl-key',
        type=str, default=None,
        help="the server's SSL private key file"
    )
    arguments = parser.parse_args()
    # Convert the port range into a range object
    try:
        if (match_ := re.match(r'^([0-9]*)-([0-9]*)$', arguments.port_range)) == None:
            raise ValueError()
        arguments.port_range = range(
            int(match_.group(1)),
            int(match_.group(2)) + 1
        )
        if len(arguments.port_range) == 0:
            raise ValueError()
    except ValueError:
        parser.error('invalid port range')
    # If SSL is desired, check if both the certificate and private key are provided
    if arguments.ssl_cert != None or arguments.ssl_key != None:
        if arguments.ssl_cert == None:
            parser.error('missing SSL certificate')
        if arguments.ssl_key == None:
            parser.error('missing SSL private key')
    return arguments

if __name__ == '__main__':
    arguments = parse_arguments()

    try:
        service = GameService(
            arguments.rpc_host,
            arguments.game_host,
            arguments.port_range,
            arguments.jwt_secret,
            arguments.ssl_cert,
            arguments.ssl_key
        )
        run(service.main_loop())
    except Exception as exception:
        print(f'fatal: {exception}', file=stderr)
    except KeyboardInterrupt:
        pass
