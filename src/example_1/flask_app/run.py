
from flask import Flask
from example_1.entrypoint import create_container
from example_1.flask_app.app import configure_app
from pocpoc.api.utils.debugging import setup_debug_logging


container = create_container()

app = Flask(__name__)


setup_debug_logging("pocpoc*", "example_1*")

configure_app(app, container.get_class_initializer())

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

