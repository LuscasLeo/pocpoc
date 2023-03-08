import logging
from flask import Flask
from example_1.entrypoint import (
    create_container,
    register_aggregated_uow_hooks,
    register_runtime_message_dispatcher,
    create_message_dispatcher_uow,
)
from example_1.flask_app.app import configure_app
from pocpoc.api.utils.debugging import setup_debug_logging


container = create_container()
register_runtime_message_dispatcher(container)
register_aggregated_uow_hooks(container, create_message_dispatcher_uow)

app = Flask(__name__)

setup_debug_logging("example_1.*", level=logging.DEBUG)

# setup_debug_logging(
#     "pocpoc*",
#     level=logging.INFO,
# )

# setup_debug_logging(
#     "flask*",
#     level=logging.INFO,
# )

configure_app(app, container.get_class_initializer())

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
