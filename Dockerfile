FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-setuptools curl && \
    pip3 install --no-cache-dir pika && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY producer.py /app/producer.py
COPY worker.py /app/worker.py
COPY publisher.py /app/publisher.py
COPY subscriber.py /app/subscriber.py
CMD ["python3", "/app/worker.py"]
