from queue import Queue
from typing import Tuple, Optional
from threading import Thread, Event
from tinyrpc.client import RPCClient, RPCProxy
from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from pika import BlockingConnection, ConnectionParameters
from tinyrpc.transports.rabbitmq import RabbitMQClientTransport

class TransmitterThread(Thread):
    RECONNECT_DELAY = 5.0

    def __init__(self, host: str) -> None:
        super().__init__(daemon=True)
        self._host = host
        self._event = Event()
        self._message_queue: Queue[Optional[Tuple[int, int, int, int]]] = Queue()

    def run(self) -> None:
        backlog = None
        while not self._event.is_set():
            try:
                # Attempt to connect to the message broker, any exception will
                # cause a delayed reconnection
                proxy = RPCClient(
                    JSONRPCProtocol(),
                    RabbitMQClientTransport(
                        BlockingConnection(
                            ConnectionParameters(self._host)
                        ),
                        'matchmaker_service_queue'
                    )
                ).get_proxy(one_way=True)
                # Dequeue messages and transmit them
                while not self._event.is_set():
                    if backlog:
                        # Prefer a message in the backlog to a new message from the queue
                        message = backlog
                    else:
                        if (message := self._message_queue.get()) == None and self._event.is_set():
                            # Return immediately when a wake-up message was dequeued or
                            # the event flag was set while waiting for a message
                            return
                    # If the message is not sent, keep it in the backlog until
                    # the next connection attempt succeeds
                    backlog = message
                    proxy.transmit_game_result(*message)
                    backlog = None
            except Exception:
                self._event.wait(TransmitterThread.RECONNECT_DELAY)

class ResultTransmitter:
    def __init__(self, host: str) -> None:
        self._thread = TransmitterThread(host)

    def transmit(self, game_id: int, winning_side: int, score_a: int, score_b: int) -> None:
        if self._thread != None:
            self._thread._message_queue.put((game_id, winning_side, score_a, score_b))

    def __enter__(self) -> None:
        if self._thread != None:
            self._thread.start()

    def __exit__(self, *_) -> None:
        # Set the event flag to make the thread break out of its loop, then put
        # None into the message queue to cancel the potential blocking wait
        self._thread._event.set()
        self._thread._message_queue.put(None)
        # Wait for the thread to finish
        self._thread.join()
        self._thread = None
