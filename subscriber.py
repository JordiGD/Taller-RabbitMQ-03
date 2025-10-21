#!/usr/bin/env python
import pika
import sys
import json
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        """Establece conexión con RabbitMQ"""
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
            
            logger.info(f"Suscriptor '{self.subscriber_name}' conectado")
            logger.info(f"Cola: {self.queue_name}")
            if self.categories:
                logger.info(f"Filtrando categorías: {', '.join(self.categories)}")
            else:
                logger.info("Recibiendo TODAS las categorías")
                
        except Exception as e:
            logger.error(f"Error conectando a RabbitMQ: {e}")
            sys.exit(1)
    
    def callback(self, ch, method, properties, body):
        """Procesa mensaje recibido"""
        try:
            message = json.loads(body.decode('utf-8'))
            
            category = message.get('category', 'UNKNOWN')
            title = message.get('title', 'Sin título')
            content = message.get('content', 'Sin contenido')
            timestamp = message.get('timestamp', 'Sin fecha')
            publisher_id = message.get('publisher_id', 'Desconocido')
            
            if self.categories and category not in self.categories:
                logger.debug(f"Mensaje filtrado - categoría '{category}' no en {self.categories}")
                return
            
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M:%S')
            except:
                formatted_time = timestamp
            
            print(f"\n [{category}] {title}")
            print(f"{formatted_time} | {self.subscriber_name}")
            print(f"{content}")
            print(f"Publisher: {publisher_id}")
            print("-" * 60)
            
        except json.JSONDecodeError:
            logger.error("Error decodificando mensaje JSON")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
    
    
    def start_consuming(self):
        """Inicia el consumo de mensajes"""
        try:
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.callback,
                auto_ack=True
            )
            
            print(f"\n{self.subscriber_name} esperando noticias...")
            print("   Presiona CTRL+C para salir\n")
            
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            print(f"\n👋 {self.subscriber_name} desconectándose...")
            self.stop_consuming()
        except Exception as e:
            logger.error(f"Error en consumo: {e}")
    
    def stop_consuming(self):
        """Detiene el consumo"""
        if self.channel:
            self.channel.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        logger.info("Suscriptor desconectado")

def main():
    if len(sys.argv) < 2:
        print("""
News Subscriber - Patrón Publish/Subscribe

Uso:
  python subscriber.py <nombre_suscriptor> [categorías...]

Ejemplos:
  python subscriber.py "Deportes Fan" SPORTS           # Solo deportes
  python subscriber.py "Tech Reader" TECH SCIENCE      # Tecnología y ciencia  
  python subscriber.py "Breaking News" BREAKING        # Solo noticias urgentes
  python subscriber.py "General Reader"                # Todas las categorías

Categorías disponibles:
  TECH, SPORTS, BREAKING, ECONOMY, HEALTH, POLITICS, SCIENCE, ENTERTAINMENT

Nota: En el patrón publish/subscribe, TODOS los suscriptores reciben TODOS 
      los mensajes del exchange. Las categorías aquí son filtros locales.
        """)
        sys.exit(1)
    
    subscriber_name = sys.argv[1]
    categories = [cat.upper() for cat in sys.argv[2:]] if len(sys.argv) > 2 else []
    
    subscriber = NewsSubscriber(subscriber_name, categories)
    subscriber.start_consuming()

if __name__ == '__main__':
    main()