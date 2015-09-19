#!/usr/bin/env bash

while : ; do
    git-multi-status $(< ~/.repo-dirs )
    sleep 2
done

