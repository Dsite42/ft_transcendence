from websockets import WebSocketServerProtocol, Headers, HeadersLike
from typing import Optional, Tuple
from jwt import decode as jwt_decode
import os

# WebsocketClient class for handling websocket connections via create_protocol and checking if the token is valid (means can be decoded)
class WebsocketClient(WebSocketServerProtocol):
    TEXT_RESPONSE_HEADERS = {'Content-Type': 'text/plain'}

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user_id: Optional[int] = None

    async def process_request(self, query: str, headers: Headers) -> Optional[Tuple[int, HeadersLike, bytes]]:
        path, _, parameters = query.partition('?')
        match path:
            case '/':
                # A game session has been requested, collect and process the token parameters
                if len(parameters) > 0:
                    for parameter in parameters.split('&'):
                        key, _, value = parameter.partition('=')
                        if key != 'with_token' or not self.process_token(value):
                            return 400, WebsocketClient.TEXT_RESPONSE_HEADERS, b'Bad Request'
                if self.user_id == None:
                    return 401, WebsocketClient.TEXT_RESPONSE_HEADERS, b'Unauthorized'
                return None
        return 404, WebsocketClient.TEXT_RESPONSE_HEADERS, b'Not Found'

    def process_token(self, token: str) -> bool:
        try:
            payload = jwt_decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
            self.user_id = payload['user_id']
        except:
            return False
        return True
