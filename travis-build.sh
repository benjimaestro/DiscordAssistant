#!/bin/bash
cat assistant.py
docker build -t zoemaestra/discord-bot .
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker-compose bundle --push-images
