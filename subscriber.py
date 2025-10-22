#!/usr/bin/env python
import pika
import sys
import json
import os
from datetime import datetime

class NewsSubscriber:
    def __init__(self, subscriber_name="subscriber", categories=None):
        self.connection = None
        self.channel = None
        self.exchange_name = 'news_fanout'
        self.subscriber_name = subscriber_name
        self.categories = categories or []
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.queue_name = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()
            
            self.channel.exchange_declare(
                exchange=self.exchange_name, 
                exchange_type='fanout',
                durable=True
            )
            
            result = self.channel.queue_declare(queue='', exclusive=True)
            self.queue_name = result.method.queue
            
            self.channel.queue_bind(
                exchange=self.exchange_name, 
                queue=self.queue_name
            )
                
        except Exception as e:
            print(f"Error conectando a RabbitMQ: {e}")
            sys.exit(1)
    
    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            
            category = message.get('category', 'UNKNOWN')
            title = message.get('title', 'Sin título')
            content = message.get('content', 'Sin contenido')
            timestamp = message.get('timestamp', 'Sin fecha')
            publisher_id = message.get('publisher_id', 'Desconocido')
            
            # Filtrar por categorías si se especificaron
            if self.categories and category not in self.categories:
                return
            
            # Formatear timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M:%S')
            except:
                formatted_time = timestamp
            
            print(f"[x] {self.subscriber_name} received [{category}] {title}")
            print(f"    Time: {formatted_time}")
            print(f"    Content: {content}")
            
        except json.JSONDecodeError:
            print("Error decodificando mensaje JSON")
        except Exception as e:
            print(f"Error procesando mensaje: {e}")
    
    def start_consuming(self):
        try:
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.callback,
                auto_ack=True
            )
            
            print(f"[*] {self.subscriber_name} waiting for messages. To exit press CTRL+C")
            if self.categories:
                print(f"[*] Filtering categories: {', '.join(self.categories)}")
            
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            self.stop_consuming()
        except Exception as e:
            print(f"Error en consumo: {e}")
    
    def stop_consuming(self):
        if self.channel:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python subscriber.py <subscriber_name> [categories...]")
        print("Example: python subscriber.py 'Sports Fan' SPORTS")
        print("Example: python subscriber.py 'Tech Reader' TECH SCIENCE")
        print("Example: python subscriber.py 'General Reader'")
        sys.exit(1)
    
    subscriber_name = sys.argv[1]
    categories = [cat.upper() for cat in sys.argv[2:]] if len(sys.argv) > 2 else []
    
    subscriber = NewsSubscriber(subscriber_name, categories)
    subscriber.start_consuming()

if __name__ == '__main__':
    main()