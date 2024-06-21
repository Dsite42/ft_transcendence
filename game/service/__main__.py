from .service import GameService

import re
from sys import stderr
from asyncio import run
from argparse import ArgumentParser, Namespace

def parse_arguments() -> Namespace:
    parser = ArgumentParser(description='')
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
    arguments = parser.parse_args()
    # Convert the port range into a range object
    try:
        if (match_ := re.match(r'^([0-9]*)-([0-9]*)$', arguments.port_range)) == None:
            raise ValueError()
        arguments.port_range = range(
            int(match_.group(1)),
            int(match_.group(2))
        )
        if len(arguments.port_range) == 0:
            raise ValueError()
    except ValueError:
        parser.error('invalid port range')
    return arguments

if __name__ == '__main__':
    arguments = parse_arguments()
    try:
        service = GameService(
            arguments.rpc_host,
            arguments.game_host,
            arguments.port_range,
            arguments.jwt_secret
        )
        run(service.main_loop())
    except Exception as exception:
        print(f'fatal: {exception}', file=stderr)
    except KeyboardInterrupt:
        pass
