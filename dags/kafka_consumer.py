import json
import logging
from kafka import KafkaConsumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_TOPIC = "decathlon.reviews.raw"
KAFKA_GROUP_ID = "decathlon-reviews-consumer"


def run_consumer(max_messages: int = 200):
    log.info("=== Kafka Consumer iniciado ===")

    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        consumer_timeout_ms=10000,  # para após 10s sem mensagens
    )

    reviews = []
    count = 0

    for message in consumer:
        review = message.value
        reviews.append(review)
        count += 1

        if count % 50 == 0:
            log.info(f"Recebidas {count} mensagens...")

        if count >= max_messages:
            break

    consumer.close()
    log.info(f"✅ Total recebido: {count} reviews")

    # Salva as mensagens consumidas
    output_path = "data/reviews_from_kafka.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

    log.info(f"✅ Salvo em {output_path}")
    log.info("=== Consumer finalizado ===")

    return reviews


if __name__ == "__main__":
    run_consumer()