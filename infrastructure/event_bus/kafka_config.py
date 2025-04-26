# Kafka configuration for event-driven communication
import os
from confluent_kafka import Producer, Consumer, KafkaError


def get_kafka_producer():
    """
    Get a configured Kafka producer instance
    """
    config = {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
        'client.id': os.getenv('SERVICE_NAME', 'lms-service'),
        'acks': 'all',  # Wait for all replicas to acknowledge
        'delivery.timeout.ms': 5000,
        'request.timeout.ms': 2000
    }

    return Producer(config)


def get_kafka_consumer(group_id, topics):
    """
    Get a configured Kafka consumer instance

    Args:
        group_id (str): Consumer group ID
        topics (list): List of topics to subscribe to
    """
    config = {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
    }

    consumer = Consumer(config)
    consumer.subscribe(topics)

    return consumer


# Define common event topics
STUDENT_ACTIVITY_TOPIC = 'student-activity'
ASSIGNMENT_CREATED_TOPIC = 'assignment-created'
ASSIGNMENT_SUBMITTED_TOPIC = 'assignment-submitted'
GRADE_POSTED_TOPIC = 'grade-posted'
NOTIFICATION_TOPIC = 'notifications'