# Backend

## Running backend locally

1. Navigate to the `app` folder
2. Run `make run-local`
3. To access the endpoints for testing, navigate to `https://0.0.0.0:8000/{route name}`

> [!NOTE]
>
> To send a request to the end point using Postman, use `http://0.0.0.0:8000/{route name}` instead as Postman rejects SSL certificate from localhost as it is self-signed.

## Running backend tests

1. Navigate to the `app` folder
2. Run `make backend-test` or `make backend-local` to run the tests on local or deployed backend respectively.

> [!NOTE]
>
> Ensure you have run `pip install requirements-dev.txt` in the root folder before running the tests as the test requires pytest modules.
