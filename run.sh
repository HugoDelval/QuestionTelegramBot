#!/bin/bash
docker build -t poll .
docker run -d --restart=unless-stopped --name poll -v $(pwd)/db:/tmp/db poll

