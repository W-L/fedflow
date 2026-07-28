#! /bin/bash

CURL_CMD=""


for i in $(seq 1 63); do
    echo "Starting VM $i"
    eval "$CURL_CMD"
    sleep 1
done
