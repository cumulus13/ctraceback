import pulsar
from pulsar import Client
# from pulsar.exceptions import PulsarClientException
import logging
# logging.getLogger("pulsar").setLevel(logging.CRITICAL)

class PulsarHandler:
    def __init__(self, service_url, username='admin', password='Xxxnuxer13'):
        self.service_url = service_url
        self.username = username
        self.password = password
        self.client = None
        self.producer = None
        self.consumer = None

    def connect(self):
        """Connect to the Pulsar service with authentication."""
        try:
            # Create a Pulsar client with username and password authentication
            # self.client = Client(self.service_url, authentication={'type': 'basic', 'params': {'username': self.username,'password': self.password}})
            self.client = Client(self.service_url, authentication=None, logger=logging.getLogger("ctraceback-pulsar"))
            print(f"Successfully connected to Pulsar at {self.service_url}")
        except Exception as e:
            print(f"Error connecting to Pulsar: {str(e)}")
            raise

    def create_producer(self, topic):
        """Create a producer to send messages."""
        if self.client is None:
            raise Exception("Client is not connected. Call connect() first.")
        
        self.producer = self.client.create_producer(topic)
        print(f"Producer created for topic: {topic}")

    def send_message(self, message):
        """Send a message using the producer."""
        if self.producer is None:
            raise Exception("Producer is not created. Call create_producer() first.")
        
        try:
            self.producer.send(message.encode('utf-8'))
            print(f"Sent message: {message}")
        except Exception as e:
            print(f"Error sending message: {str(e)}")
    
    def create_consumer(self, topic, subscription):
        """Create a consumer to receive messages."""
        if self.client is None:
            raise Exception("Client is not connected. Call connect() first.")
        
        self.consumer = self.client.subscribe(topic, subscription)
        print(f"Consumer created for topic: {topic} with subscription: {subscription}")

    def receive_message1(self):
        """Receive a message using the consumer."""
        if self.consumer is None:
            raise Exception("Consumer is not created. Call create_consumer() first.")
        
        try:
            msg = self.consumer.receive()
            print(f"Received message: {msg.data().decode('utf-8')}")
            self.consumer.acknowledge(msg)
        except Exception as e:
            print(f"Error receiving message: {str(e)}")
            
    def receive_message(self):
        try:
            while True:  # Continuous loop
                msg = self.consumer.receive()
                print(f"Received message: {msg.data().decode('utf-8')}")
                self.consumer.acknowledge(msg)
        except KeyboardInterrupt:
            print("Stopping consumer...")
        finally:
            self.close()
    
    def close(self):
        """Close the Pulsar client and associated resources."""
        if self.client:
            self.client.close()
            print("Pulsar client closed.")

# Example usage
if __name__ == "__main__":
    pulsar_handler = PulsarHandler(service_url="pulsar://192.168.100.2:6650", username="admin", password="Xxxnuxer13")
    
    # Connect to Pulsar with authentication
    pulsar_handler.connect()

    # Create producer and send a message
    # pulsar_handler.create_producer("persistent://public/default/my-topic")
    # pulsar_handler.send_message("Hello, Pulsar!")

    # Create consumer and receive messages
    pulsar_handler.create_consumer("persistent://public/default/my-topic", "my-subscription")
    pulsar_handler.receive_message()

    # Close the client connection
    pulsar_handler.close()
