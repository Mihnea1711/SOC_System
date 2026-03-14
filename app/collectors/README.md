# see topics
docker exec -it kafka \
  /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list

# consume messages from filebeat
docker exec -it kafka \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic raw.logs \
  --from-beginning

# consume messages from filebeat
docker exec -it kafka \
  /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9094 \
  --topic raw.packets \
  --from-beginning

# test access.log
docker exec -it monitored_host sh -c 'echo "kafka test $(date)" >> /var/log/nginx/access.log' 
## should appear on kafka raw.logs