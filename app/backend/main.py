from dotenv import load_dotenv

from app import create_app

app = create_app()

if __name__ == "__main__":
    load_dotenv("../.azure/hhgai-dev-eastus-001/.env")
    app.run(host="0.0.0.0", port=8000, debug=True)
