#!/bin/sh

echo ""
echo "Loading azd .env file from current environment"
echo ""

while IFS='=' read -r key value; do
    value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')
    export "$key=$value"
done <<EOF
$(azd env get-values)
EOF

if [ $? -ne 0 ]; then
    echo "Failed to load environment variables from azd environment"
    exit $?
fi


func_backend() {
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
}


func_frontend() {
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

}

func_frontend_build() {
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

  npm run build:live
  if [ $? -ne 0 ]; then
      echo "Failed to build frontend"
      exit $?
  fi
}


trap "kill 0" EXIT
func_backend&
func_frontend&
wait
