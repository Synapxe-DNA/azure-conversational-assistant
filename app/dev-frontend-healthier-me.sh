#!/bin/sh

echo ""
echo "Restoring frontend npm packages"
echo ""


cd ./frontend-healthier-me
npm install
if [ $? -ne 0 ]; then
    echo "Failed to restore frontend npm packages"
    exit $?
fi

echo ""
echo "Starting frontend"
echo ""

npm run start
if [ $? -ne 0 ]; then
    echo "Failed to build frontend"
    exit $?
fi

