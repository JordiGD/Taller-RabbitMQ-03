#!/usr/bin/env python
import pika
import sys
import json
import time
from datetime import datetime
import os

class NewsPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange_name = 'news_fanout'
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
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
            
        except Exception as e:
            print(f"Error conectando a RabbitMQ: {e}")
            sys.exit(1)
    
    def publish_news(self, category, title, content):
        try:
            message = {
                'timestamp': datetime.now().isoformat(),
                'category': category,
                'title': title,
                'content': content,
                'publisher_id': 'news-publisher-001'
            }
            
            message_body = json.dumps(message, ensure_ascii=False)
            
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key='',
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            
            print(f"[x] Sent [{category}] {title}")
            return True
            
        except Exception as e:
            print(f"Error publicando mensaje: {e}")
            return False
    
    def publish_breaking_news(self, title, content):
        return self.publish_news("BREAKING", title, content)
    
    def simulate_news_feed(self, count=5):
        news_samples = [
            ("TECH", "Nueva versión de Python lanzada", "Python 3.12 incluye mejoras significativas en rendimiento"),
            ("SPORTS", "Final de la Champions League", "Real Madrid vs Barcelona en la final más esperada"),
            ("BREAKING", "Descubrimiento científico importante", "Nuevos avances en computación cuántica"),
            ("ECONOMY", "Mercados en alza", "Las bolsas mundiales registran ganancias generalizadas"),
            ("HEALTH", "Nuevo tratamiento aprobado", "FDA aprueba innovador tratamiento para diabetes"),
            ("TECH", "Inteligencia Artificial en medicina", "IA ayuda en diagnóstico temprano de enfermedades"),
            ("SPORTS", "Récord mundial batido", "Atleta rompe récord en maratón olímpico")
        ]
        
        for i in range(count):
            if i < len(news_samples):
                category, title, content = news_samples[i]
            else:
                category, title, content = news_samples[i % len(news_samples)]
                title += f" (#{i+1})"
            
            self.publish_news(category, title, content)
            time.sleep(2)
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

def main():
    publisher = NewsPublisher()
    
    try:
        if len(sys.argv) == 1:
            publisher.simulate_news_feed(10)
            
        elif len(sys.argv) == 2 and sys.argv[1] == '--breaking':
            title = input("Título de la noticia de última hora: ")
            content = input("Contenido: ")
            publisher.publish_breaking_news(title, content)
            
        elif len(sys.argv) >= 4:
            category = sys.argv[1].upper()
            title = sys.argv[2]
            content = ' '.join(sys.argv[3:])
            publisher.publish_news(category, title, content)
            
        else:
            print("Usage: python publisher.py [category] [title] [content]")
            print("       python publisher.py --breaking")
            print("       python publisher.py  (simulation mode)")
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        publisher.close()

if __name__ == '__main__':
    main()