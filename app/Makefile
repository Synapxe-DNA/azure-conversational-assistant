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

ssl-cert: # Create ssl for local development
	openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

backend-test: # Run backend test
	python backend/test/pytest_main.py
