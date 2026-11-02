import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # start.bat sets AGGREGATOR_DEBUG=0 for demonstrations.
    debug = os.environ.get("AGGREGATOR_DEBUG", "1") == "1"
    app.run(debug=debug, port=5000)
