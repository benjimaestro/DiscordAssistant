#!/bin/bash
docker-compose build
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker-compose push
