from __future__ import absolute_import, unicode_literals
import os
from pulsar import Client, Producer, Consumer, AuthenticationToken
import contextlib
from pathlib import Path
from rich.text import Text
from rich import traceback as rich_traceback
import shutil
rich_traceback.install(width=shutil.get_terminal_size()[0], theme='fruity')
import tenacity
import os
from pydebugger.debug import debug
from datetime import datetime
import importlib
import logging

spec_config = importlib.util.spec_from_file_location("config", str(Path(__file__).parent.parent / 'config.py'))
config = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(config)

CONFIG = config.CONFIG

from rich.console import Console
console = Console(theme=CONFIG().severity_theme)


class PulsarHandler:
    def __init__(self, tenant=None, namespace=None, topic=None, sub = None, auth_token=None, host = None, port = None, verbose = ""):
        self.config = CONFIG()
        self.tenant = tenant or self.config.PULSAR_TENANT or 'ctraceback_tenant'
        self.namespace = namespace or self.config.PULSAR_NAMESPACE or 'ctraceback_namespace'
        self.topic = topic or self.config.PULSAR_TOPIC or 'ctraceback_topic'
        self.sub = sub or self.config.PULSAR_SUB or 'ctraceback_sub'
        self.auth_token = auth_token or self.config.PULSAR_AUTH_TOKEN or os.getenv('PULSAR_AUTH_TOKEN')
        self.host = host or self.config.PULSAR_HOST or 'localhost'
        self.port = port or self.config.PULSAR_PORT or 6650
        self.pulsar_url = os.getenv('PULSAR_URL') or f'pulsar://{self.host}:{self.port}'
        self.client = None
        self.producer = None
        self.consumer = None
        self.CURRENT_HEIGHT = 0
        self.VERBOSE = self.config.PULSAR_VERBOSE or self.config.VERBOSE

    def connect(self):
        auth = None
        if self.auth_token: auth = AuthenticationToken(self.auth_token)

        self.client = Client(self.pulsar_url, authentication=auth, logger=logging.getLogger("ctraceback-pulsar") if not self.VERBOSE else None)

    def close(self):
        if self.client: self.client.close()

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3), reraise=True)
    def create_producer(self):
        if not self.client: self.connect()

        full_topic = f"persistent://{self.tenant}/{self.namespace}/{self.topic}"
        self.producer = self.client.create_producer(full_topic)

    def send(self, body, verbose=False):
        verbose = verbose or self.VERBOSE
        if not self.producer: self.create_producer()

        if verbose: print(f"Sending message to topic {self.topic}: {body}")

        self.producer.send(body.encode('utf-8'))

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3), reraise=True)
    def create_consumer(self, subscription_name=None):
        subscription_name = subscription_name or self.sub
        if not self.client: self.connect()

        full_topic = f"persistent://{self.tenant}/{self.namespace}/{self.topic}"
        self.consumer = self.client.subscribe(full_topic, subscription_name)

    def consume(self, callback=None, subscription_name=None, verbose=False):
        verbose = verbose or self.VERBOSE
        subscription_name = subscription_name or self.sub
        if not self.consumer: self.create_consumer(subscription_name)

        if verbose: print(f"Consuming messages from topic {self.topic} with subscription {subscription_name} ...")
        try:
            while True:
                msg = self.consumer.receive()
                body = msg.data().decode('utf-8')
                self.CURRENT_HEIGHT += 1

                if callback:
                    callback(body)
                else:
                    if verbose: print(f"Received message: {body}")

                self.consumer.acknowledge(msg)
        except KeyboardInterrupt:
            print("Stopping consumer...")
        finally:
            self.close()
