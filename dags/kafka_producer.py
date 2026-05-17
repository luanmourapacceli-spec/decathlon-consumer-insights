import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = "localhost:9092"
KAFKA_TOPIC = "decathlon.reviews.raw"


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
        retries=3,
        compression_type="gzip",
    )


def load_reviews(path: str = "data/reviews_synthetic.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def publish_reviews(reviews: list[dict], producer: KafkaProducer) -> None:
    success, failed = 0, 0

    for review in reviews:
        try:
            future = producer.send(
                topic=KAFKA_TOPIC,
                key=review["store_id"],
                value=review,
            )
            future.get(timeout=10)
            success += 1

            if success % 50 == 0:
                log.info(f"Publicadas {success} reviews...")

        except KafkaError as e:
            log.error(f"Falha ao publicar {review['review_id']}: {e}")
            failed += 1

    producer.flush()
    log.info(f"✅ Concluído: {success} publicadas | {failed} falhas")


if __name__ == "__main__":
    log.info("=== Kafka Producer iniciado ===")
    log.info(f"Tópico: {KAFKA_TOPIC}")

    reviews = load_reviews()
    log.info(f"Reviews carregadas: {len(reviews)}")

    producer = create_producer()
    try:
        publish_reviews(reviews, producer)
    finally:
        producer.close()

    log.info("=== Producer finalizado ===")
    