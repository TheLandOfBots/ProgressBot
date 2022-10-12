#!/bin/sh

docker run --env-file .env --volume `pwd`/data/:/app/data/ igorpidik/progress_bot:latest
