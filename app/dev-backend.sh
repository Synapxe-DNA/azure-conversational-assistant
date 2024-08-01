#!/bin/sh

cd ../
echo 'Creating python virtual environment ".venv"'
python3 -m venv .venv

echo ""
echo "Restoring backend python packages"
echo ""

cd ./app/backend

echo ""
echo "Starting backend"
echo ""

port=50505
host=localhost
../../.venv/bin/python -m quart --app main:app run --port "$port" --host "$host" --reload
if [ $? -ne 0 ]; then
    echo "Failed to start backend"
    exit $?
fi
