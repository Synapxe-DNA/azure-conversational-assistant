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

backend-test: # Run backend tests using deployed API endpoint. Indicate FILE=<TEST FILE PATH> to run specific test file
	@read -p "Enter the endpoint you want to test (e.g speech, feedback) [or press Enter to skip and run all test files]: " endpoint; \
	if [ -n "$$endpoint" ]; then \
		read -p "Enter the function you want to test (e.g valid_json_test) [or press Enter to skip and run all functions]: " function; \
		if [ -n "$$function" ]; then \
			fullpath=$$endpoint"_test.py"::$$function; \
		else \
			fullpath=$$endpoint"_test.py"; \
		fi; \
		echo "Running test for $$fullpath"; \
		cd backend/test && pytest -v "$$fullpath" -n 5; \
	else \
		echo "Running all tests."; \
		cd backend/test && pytest -v -n 5; \
	fi

backend-test-local: # Run backend tests using local API endpoint
	@read -p "Enter the endpoint you want to test (e.g speech, feedback) [or press Enter to skip and run all test files]: " endpoint; \
	if [ -n "$$endpoint" ]; then \
		read -p "Enter the function you want to test (e.g valid_json_test) [or press Enter to skip and run all functions]: " function; \
		if [ -n "$$function" ]; then \
			fullpath=$$endpoint"_test.py"::$$function; \
		else \
			fullpath=$$endpoint"_test.py"; \
		fi; \
		echo "Running test for $$fullpath"; \
		cd backend/test && pytest -v --local "$$fullpath" -n 5; \
	else \
		echo "Running all tests."; \
		cd backend/test && pytest -v --local -n 5; \
	fi
