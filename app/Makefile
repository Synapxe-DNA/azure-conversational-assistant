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

set-env:
	azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT_VERSION 2024-05-13
	azd env set AZURE_OPENAI_EMB_DEPLOYMENT_VERSION 1
	azd env set USE_SPEECH_INPUT_BROWSER true
	azd env set USE_SPEECH_OUTPUT_BROWSER true
	azd env set USE_SPEECH_OUTPUT_AZURE true
