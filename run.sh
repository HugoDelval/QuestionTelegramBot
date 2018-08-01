#!/bin/bash
docker build -t poll .
mkdir -p db
docker run -d --restart=unless-stopped --env-file docker.env --name poll -v $(pwd)/db:/tmp/db poll

