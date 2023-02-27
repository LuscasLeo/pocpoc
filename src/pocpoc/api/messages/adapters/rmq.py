from pika import BlockingConnection, PlainCredentials, ConnectionParameters


class RMQConnectionFactory:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def get_connection(self) -> BlockingConnection:
        return BlockingConnection(
            ConnectionParameters(
                credentials=PlainCredentials(self.username, self.password),
                host=self.host,
                port=self.port,
                heartbeat=120,
            ),
        )
