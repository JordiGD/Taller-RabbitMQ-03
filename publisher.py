import pika
import sys
import json
import time
from datetime import datetime
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NewsPublisher:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange_name = 'news_fanout'
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
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
            logger.info(f"Conectado a RabbitMQ en {self.host}")
            logger.info(f"Exchange '{self.exchange_name}' declarado como fanout")
            
        except Exception as e:
            logger.error(f"Error conectando a RabbitMQ: {e}")
            sys.exit(1)
    
    def publish_news(self, category, title, content):
        """Publica una noticia que será recibida por todos los suscriptores"""
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
            
            logger.info(f"Noticia publicada: [{category}] {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error publicando mensaje: {e}")
            return False
    
    def publish_breaking_news(self, title, content):
        """Publica noticia de última hora"""
        return self.publish_news("BREAKING", title, content)
    
    def simulate_news_feed(self, count=5):
        """Simula un feed de noticias publicando varias noticias"""
        news_samples = [
            ("TECH", "Nueva versión de Python lanzada", "Python 3.12 incluye mejoras significativas en rendimiento"),
            ("SPORTS", "Final de la Champions League", "Real Madrid vs Barcelona en la final más esperada"),
            ("BREAKING", "Descubrimiento científico importante", "Nuevos avances en computación cuántica"),
            ("ECONOMY", "Mercados en alza", "Las bolsas mundiales registran ganancias generalizadas"),
            ("HEALTH", "Nuevo tratamiento aprobado", "FDA aprueba innovador tratamiento para diabetes"),
            ("TECH", "Inteligencia Artificial en medicina", "IA ayuda en diagnóstico temprano de enfermedades"),
            ("SPORTS", "Récord mundial batido", "Atleta rompe récord en maratón olímpico")
        ]
        
        logger.info(f"Iniciando simulación de {count} noticias...")
        
        for i in range(count):
            if i < len(news_samples):
                category, title, content = news_samples[i]
            else:
                category, title, content = news_samples[i % len(news_samples)]
                title += f" (#{i+1})"
            
            self.publish_news(category, title, content)
            time.sleep(2)
    
    def close(self):
        """Cierra la conexión"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Conexión cerrada")

def main():
    publisher = NewsPublisher()
    
    try:
        if len(sys.argv) == 1:
            print("Modo simulación activado - publicando noticias automáticamente...")
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
            print("""
News Publisher - Patrón Publish/Subscribe

Uso:
  python publisher.py                                    # Modo simulación (10 noticias)
  python publisher.py --breaking                         # Noticia de última hora interactiva
  python publisher.py TECH "Nueva tecnología" "Contenido de la noticia"

Ejemplos:
  python publisher.py SPORTS "Final del Mundial" "Partido decisivo esta noche"
  python publisher.py BREAKING "Noticia urgente" "Información importante"
  python publisher.py ECONOMY "Mercados" "Análisis económico del día"

Categorías sugeridas: TECH, SPORTS, BREAKING, ECONOMY, HEALTH, POLITICS
            """)
            
    except KeyboardInterrupt:
        logger.info("Publicación interrumpida por el usuario")
    except Exception as e:
        logger.error(f"Error en el publisher: {e}")
    finally:
        publisher.close()

if __name__ == '__main__':
    main()