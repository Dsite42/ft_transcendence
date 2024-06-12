#!/usr/bin/env python3

# encode_jwt.py: Produces a JWT token for authorization
# This script is meant for authorization testing and won't be used during normal runtime

from argparse import ArgumentParser
from jwt import encode as jwt_encode

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-j', '--jwt-secret', type=str, required=True)
    parser.add_argument('-I', '--user-id', type=int, required=True)
    arguments = parser.parse_args()
    print(jwt_encode({'user_id': arguments.user_id}, arguments.jwt_secret, 'HS256'))
