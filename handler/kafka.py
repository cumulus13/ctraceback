from kafka import KafkaProducer, KafkaConsumer
import json
import os
from datetime import datetime
import tenacity

class KafkaHandler:
    def __init__(self, topic_name='ctraceback', bootstrap_servers=None, group_id=None, auto_offset_reset='earliest'):
        self.config = CONFIG()
        self.topic_name = topic_name or self.config.KAFKA_TOPIC_NAME or os.getenv('KAFKA_TOPIC_NAME')
        self.bootstrap_servers = bootstrap_servers or self.config.KAFKA_BOOTSTRAP_SERVERS or os.getenv('KAFKA_BOOTSTRAP_SERVERS') or 'localhost:9092'
        self.group_id = group_id or self.config.KAFKA_GROUP_ID or os.getenv('KAFKA_GROUP_ID') or 'group1'
        self.auto_offset_reset = auto_offset_reset
        self.producer = None
        self.consumer = None
        self.CURRENT_HEIGHT = 0

    def create_producer(self):
        if not self.producer:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )

    def create_consumer(self):
        if not self.consumer:
            self.consumer = KafkaConsumer(
                self.topic_name,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )

    def call_back(self, message):
        data = message.value
        self.CURRENT_HEIGHT += 1

        def get_date():
            return datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f')

        print(
            f"{str(self.CURRENT_HEIGHT).zfill(2)} {get_date()} {data}"
        )

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3), reraise=True)
    def send(self, body, verbose=False):
        self.create_producer()
        if verbose:
            print(f"Sending message to topic {self.topic_name}...")
        self.producer.send(self.topic_name, body)
        self.producer.flush()

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3), reraise=True)
    def consume(self, call_back=None, verbose=False):
        call_back = call_back or self.call_back
        self.create_consumer()
        if verbose:
            print(f"Consuming messages from topic {self.topic_name}...")
        try:
            for message in self.consumer:
                call_back(message)
        except KeyboardInterrupt:
            print("Exiting consumer...")
        finally:
            self.close()

    def close(self):
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()
