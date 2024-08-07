#!/bin/sh

apt install ffmpeg -y
python3 -m gunicorn main:app
