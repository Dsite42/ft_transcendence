from .server import Server
from .notifier import FileNotifier, NullNotifier

from sys import stderr
from asyncio import run
from argparse import ArgumentParser, Namespace

def process_arguments() -> Namespace:
    parser = ArgumentParser(description='Serves a game session')
    parser.add_argument(
        '-H', '--host',
        type=str, default='0.0.0.0',
        help="the server's listening host, defaults to any (0.0.0.0)"
    )
    parser.add_argument(
        '-p', '--port',
        type=int, required=True,
        help="the server's listening port"
    )
    parser.add_argument(
        '-j', '--jwt-secret',
        type=str, required=True,
        help="the secret used to validate a JWT token's authenticity"
    )
    parser.add_argument(
        '-r', '--tick-rate',
        type=float, default=32.0,
        help="the amount of game ticks per second, defaults to 32"
    )
    parser.add_argument(
        '-I', '--player-ids',
        type=int, nargs=2, required=True,
        help="user IDs (2) that are considered as players (must be unique, -1 for guest)"
    )
    parser.add_argument(
        '-n', '--notify-fd',
        type=int, default=-1,
        help="file descriptor"
    )
    arguments = parser.parse_args()
    # Check if the given port is valid
    if arguments.port < 0 or arguments.port > 65535:
        parser.error('invalid port, must be within unsigned 16-bit integer range')
    # Check if the given player IDs are valid
    if len(set(arguments.player_ids)) != 2:
        parser.error('player IDs must be unique')
    for player_id in arguments.player_ids:
        if player_id < 0 and player_id != -1:
            parser.error('player IDs must be positive or -1 for guest')
    # Check if the given notify file descriptor is valid
    if arguments.notify_fd < -1:
        parser.error('bad notify file descriptor')
    return arguments

if __name__ == '__main__':
    arguments = process_arguments()
    try:
        if arguments.notify_fd >= 0:
            notifier = FileNotifier.from_raw_fd(arguments.notify_fd)
        else:
            notifier = NullNotifier()
        server = Server(
            arguments.host,
            arguments.port,
            arguments.jwt_secret,
            arguments.tick_rate,
            arguments.player_ids,
            notifier
        )
        run(server.main_loop())
    except Exception as exception:
        print(f'fatal: {exception}', file=stderr)
    except KeyboardInterrupt:
        pass
