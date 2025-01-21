from __future__ import absolute_import, unicode_literals
import sys
from ctraceback import CTraceback
from configset import configset
from pathlib import Path
from rich.text import Text

import json
import pika
import tenacity
from tenacity import retry, stop_after_delay, wait_fixed
import os
from amqp import Connection, Message
import socket
import re
from pydebugger.debug import debug
from kombu import Connection, Exchange, Queue
import logging
from datetime import datetime
from make_colors import make_colors
sys.path.append(str(Path(__file__).parent.parent))
import shutil

try:
    from . config import CONFIG
except:
    from config import CONFIG

def send_log_to_rabbitmq(log_message):
    config = CONFIG()
    debug(log_message = log_message)
    try:
        exchange = Exchange(
            config.get_config(
                'rabbitmq', 
                'exchange_name') or 'ctraceback', 
                type=config.get_config('rabbitmq', 'exchange_type') or 'fanout', 
                durable=config.get_config('rabbitmq', 'durable') or True
            )
        queue = Queue(name='', exchange=exchange, routing_key=config.get_config('rabbitmq', 'routing_key') or '', durable=config.get_config('rabbitmq', 'durable') or True)
        username = config.get_config('rabbitmq', 'username') or 'guest'
        password = config.get_config('rabbitmq', 'password') or 'guest'
        host = config.get_config('rabbitmq', 'host') or '127.0.0.1'
        port = int(config.get_config('rabbitmq', 'port') or 5672)
        
        with Connection(f'amqp://{username}:{password}@{host}:{port}//') as conn:
            with conn.Producer(serializer='json') as producer:
                producer.publish(
                    log_message,
                    exchange=exchange,
                    routing_key='',
                    delivery_mode=2,
                    mandatory=True,
                    priority=0,
                    expiration=None,
                    headers=None,
                    retry=True,
                    declare=[queue],
                )
    except:
        CTraceback(*sys.exc_info())

class RabbitMQHandler:
    def __init__(self, exchange_name='ctraceback', exchange_type=None, durable=True, username=None, password=None, host=None, port=None):
        self.config = CONFIG()
        self.exchange_name = exchange_name or self.config.RABBITMQ_EXCHANGE_NAME or os.getenv('RABBITMQ_EXCHANGE_NAME')
        self.exchange_type = exchange_type or self.config.RABBITMQ_EXCHANGE_TYPE or os.getenv('RABBITMQ_EXCHANGE_TYPE')
        self.durable = durable or self.config.RABBITMQ_DURABLE or os.getenv('RABBITMQ_DURABLE')
        self.username = username or self.config.RABBITMQ_USERNAME or os.getenv('RABBITMQ_USERNAME') or 'guest'
        self.password = password or self.config.RABBITMQ_PASSWORD or os.getenv('RABBITMQ_PASSWORD') or 'guest'
        self.host = host or self.config.RABBITMQ_HOST or os.getenv('RABBITMQ_HOST') or '127.0.0.1'
        self.port = port or self.config.RABBITMQ_PORT or os.getenv('RABBITMQ_PORT') or 5672
        self.routing_keys = list(filter(None, [i.strip() for i in os.getenv('RABBITMQ_ROUTING_KEY').split()])) if os.getenv('RABBITMQ_ROUTING_KEY') else self.config.RABBITMQ_ROUTING_KEY or ['ctraceback.error', 'ctraceback.100']
        self.connection = None
        self.channel = None
        # self.connect()
        
        self.CURRENT_HEIGHT = 0
        
    def call_back(self, ch, met, prop, body):
        debug(body = body)
        data = body.decode() if hasattr(body, 'decode') else body
        debug(data = data)
        self.CURRENT_HEIGHT += 1

        def get_date():
            data1 = make_colors(datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S.%f'), 'lc')
            return data1
        
        print(
            make_colors(str(self.CURRENT_HEIGHT).zfill(2), 'lw', 'bl') + " " + \
            get_date() + " " + data.decode() if hasattr(data, 'decode') else data
        )
        
        ch.basic_ack(delivery_tag = met.delivery_tag)

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3), reraise=True)
    def connect(self, verbose = False):
        debug(self_username = self.username, debug = verbose)
        debug(self_password = self.password, debug = verbose)
        debug(self_host = self.host, debug = verbose)
        debug(self_port = self.port, debug = verbose)

        credentials = pika.PlainCredentials(self.username, self.password)
        debug(credentials = credentials, debug = verbose)
        parameters = pika.ConnectionParameters(host=self.host, port=self.port, credentials=credentials)
        debug(parameters = parameters, debug = verbose)
        
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type=self.exchange_type,
            durable=self.durable,
        )
        
        self.channel.queue_declare(queue=f'ctraceback_last_{self.config.RABBITMQ_MAX_LENGTH or 100}_queue', durable=True, arguments={'x-max-length': self.config.RABBITMQ_MAX_LENGTH or 100})
        self.channel.queue_declare(queue='ctraceback_queue', durable=self.durable)
        
        self.channel.queue_bind(exchange=self.exchange_name, queue=f'ctraceback_last_{self.config.RABBITMQ_MAX_LENGTH or 100}_queue', routing_key='ctraceback.100')
        self.channel.queue_bind(exchange=self.exchange_name, queue='ctraceback_queue', routing_key='ctraceback.error')

    def send(self, body, verbose = False):
        self.connect(verbose)
        for key in self.routing_keys:
            self.channel.basic_publish(exchange=self.exchange_name, routing_key=key, body=body.encode('utf-8') if not isinstance(body, bytes) else body)
            
    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(3), reraise=True)
    def consume(self, call_back = None, last=True, verbose = False):
        call_back = call_back or self.call_back
        self.connect(verbose)
        if last:
            queue = self.channel.queue_declare(queue=f'ctraceback_last_{self.config.RABBITMQ_MAX_LENGTH or 100}_queue', durable=True, arguments={'x-max-length': self.config.RABBITMQ_MAX_LENGTH or 100})
            self.channel.queue_bind(exchange=self.exchange_name, queue=f'ctraceback_last_{self.config.RABBITMQ_MAX_LENGTH or 100}_queue', routing_key='ctraceback.100')
        
        else:
            queue = self.channel.queue_declare(queue='ctraceback_queue', durable=self.durable)
            self.channel.queue_bind(exchange=self.exchange_name, queue='ctraceback_queue', routing_key='ctraceback.error')
        
        tag = self.config.RABBITMQ_CONSUMER_TAG[0] if isinstance(self.config.RABBITMQ_CONSUMER_TAG, list) else self.config.RABBITMQ_CONSUMER_TAG or 'all'
        debug(tag = tag, debug = verbose)
        self.channel.basic_consume(queue = queue.method.queue, consumer_callback = call_back, consumer_tag=tag, no_ack = self.config.RABBITMQ_ACK)
        #channel.basic_recover(requeue = True)
        try:
            while 1:
                try:
                    self.channel.start_consuming()
                    break
                except KeyboardInterrupt:
                    print("exit ...")
                    break
                except:
                    CTraceback(*sys.exc_info())
        except KeyboardInterrupt:
            print("exit ...")
        except:
            CTraceback(*sys.exc_info())        

        self.close()

    def close(self):
        try:
            self.connection.close()
        except Exception:
            pass

class RabbitMQHandler2():
    def __init__(self, host = '127.0.0.1', port = 5672, username = 'guest', password = 'guest', exchange = 'ctraceback', routing_key = '', max_retries=3, durable = True, exchange_type = 'fanout', delivery_mode = 2):
        self.host = self.config.get_config('rabbitmq', 'host') or host
        self.port = int(self.config.get_config('rabbitmq', 'port') or port or 5672)
        self.username = self.config.get_config('rabbitmq', 'username') or username
        self.password = self.config.get_config('rabbitmq', 'password') or password
        self.exchange = self.config.get_config('rabbitmq', 'exchange_name') or exchange
        self.exchange_type = self.config.get_config('rabbitmq', 'exchange_type') or exchange_type or 'fanout'
        self.routing_key = self.config.get_config('rabbitmq', 'routing_key') or routing_key
        self.max_retries = self.config.get_config('rabbitmq', 'max_tries') or max_retries
        self.connection = None
        self.channel = None
        self.durable = self.config.get_config('rabbitmq', 'durable') or durable
        self.delivery_mode = self.config.get_config('rabbitmq', 'delivery_mode') or delivery_mode

    def connect(self):
        credentials = pika.PlainCredentials(self.username, self.password)
        parameters = pika.ConnectionParameters(self.host, self.port, '/', credentials, heartbeat=0)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange, durable=self.durable, exchange_type=self.exchange_type)

    def close(self):
        if self.connection: self.connection.close()

    def send(self, record):
        try:
            self.retry_send(record)
        except Exception as e:
            print(f'Error while sending log to RabbitMQ: {e}')

    @retry(stop=stop_after_delay(60), wait=wait_fixed(10))
    def retry_send(self, logentry):
        if not self.connection or self.connection.is_closed:
            self.connect()
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.routing_key,
            body=logentry,
            properties=pika.BasicProperties(delivery_mode=self.delivery_mode)
        )

class RabbitMQHandler3():

    def send(self, message):
        # send_log_to_rabbitmq.delay({'message': message})
        send_log_to_rabbitmq({'message': message})

class AMQPHandlerConfigError(Exception):
    pass

class AMQPHandler():
    def __init__(self, connection_url = None, exchange_name = None, exchange_type = None, username = None, password = None, durable = None):
        self.config = CONFIG()
        self.connection_url = connection_url or self.config.get_config('rabbitmq', 'url')
        if self.connection_url:
            self.exchange_name = exchange_name or self.config.get_config('rabbitmq', 'exchange_name')
            self.connection = Connection(connection_url, userid=username or self.config.get_config('rabbitmq', 'username'), password=password or self.config.get_config('rabbitmq', 'password'))
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange_name, exchange_type, durable=durable or self.config.get_config('rabbitmq', 'durable') or True)
        else:
            self.channel = None

    def send(self, message):
        if self.channel:
            self.channel.basic_publish(message, exchange=self.exchange_name)
        else:
            raise AMQPHandlerConfigError(Text("Please check configuration !", style = "white on red blink"))

class SysLogJSONHandler(logging.handlers.SysLogHandler):
    def __init__(self, *args, **kwargs):
        self.env = kwargs.get('env')
        #self.server_host = kwargs.get('server_host')
        kwargs.pop('env', None)
        #kwargs.pop('server_host', None)
        super().__init__(*args, **kwargs)
        self.sock = None

    def send(self, message):
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message = json.dumps(message)
        if isinstance(message, str):
            message = message.encode('utf-8')
        self.sock.sendto(message, self.address)

    def emit(self, record):
        pattern = r"^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2},\d{3}"
        timestamp = re.findall(pattern, self.format(record))
        if timestamp:
            timestamp = timestamp[0]
        else:
            timestamp = self.format(record)
        try:
            log_entry = {
                'timestamp': timestamp,
                'levelname': record.levelname,
                'pid': record.process,
                'tid': record.thread,
                'filename': record.filename,
                'lineno': record.lineno,
                'message': record.getMessage(),
                'logmessage': self.format(record),
                'env': self.env,
                #'client_ip': self.get_client_ip(),
                #'server_ip': self.get_server_ip(),
            }
            self.send_json(log_entry)
        except Exception:
            self.handleError(record)

    def send_json(self, log_entry):
        message = json.dumps(log_entry)
        self.send(message)

    def get_client_ip(self):
        try:
            return socket.gethostbyaddr(self.address[0])[0]
        except Exception:
            return None

    def get_server_ip(self):
        try:
            return socket.gethostbyname(self.server_host)
        except Exception:
            return None

if __name__ == '__main__':
    pass