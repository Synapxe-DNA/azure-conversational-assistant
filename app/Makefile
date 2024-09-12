run-local:
	cd frontend && npm run build
	cd ..
	python backend/main.py

run-local-backend:
	python backend/main.py

run-local-frontend:
	cd frontend && npm run build
	cd ..

lint:
	pre-commit run --all-files

set-env: # Manually set environment variables for Azure
	azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT_VERSION 2024-05-13
	azd env set AZURE_OPENAI_EMB_DEPLOYMENT_VERSION 1
	azd env set USE_SPEECH_INPUT_BROWSER true
	azd env set USE_SPEECH_OUTPUT_BROWSER true
	azd env set USE_SPEECH_OUTPUT_AZURE true
	azd env set AZURE_FEEDBACK_DATABASE_ID feedbacks
	azd env set AZURE_FEEDBACK_CONTAINER_ID feedbacks
	azd env set AZURE_COSMOS_URL https://cosmos-zicuh2lqrbb2s.documents.azure.com:443/

ssl-cert: # Create ssl for local development
	openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
