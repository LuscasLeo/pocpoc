import random
import string
from datetime import datetime
from typing import Callable, Dict, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit
import croniter

from flask import Flask, Response, render_template_string, request
from typing_extensions import Protocol

from example_2_scheduler.domain import PeriodicTrigger, get_next_run_at

TASKS_GETTER = Callable[[], Dict[str, PeriodicTrigger]]

TASKS_LAST_RUN_GETTER = Callable[[str], Optional[datetime]]


class AppInformationProvider(Protocol):
    def get_tasks(self) -> Dict[str, PeriodicTrigger]:
        pass

    def get_tasks_last_run_at(self, task_name: str) -> Optional[datetime]:
        pass

    def get_app_started_at(self) -> datetime:
        pass

    def get_next_check_time(self) -> Optional[datetime]:
        pass


class TaskManagementProvider(Protocol):
    def insert_task(self, task_name: str, task: PeriodicTrigger) -> None:
        pass


def create_app(
    info_provider: AppInformationProvider,
    task_management_provider: TaskManagementProvider,
) -> Flask:
    app = Flask(__name__)

    def index() -> Response:
        now = datetime.now().replace(microsecond=0)

        remaining_seconds_to_next_check = (
            (info_provider.get_next_check_time() or now) - now
        ).total_seconds()

        light_green_rgb = (200, 255, 200)
        light_grey_rgb = (230, 230, 230)

        min_color = light_grey_rgb
        max_color = light_green_rgb

        def get_color(value: int) -> Tuple[str, str, str]:
            return tuple(  # type: ignore
                str(int(min_color[i] + (max_color[i] - min_color[i]) * value / 100))
                for i in range(3)
            )

        def get_rgb_background_color(value: int) -> str:
            return "rgb({})".format(", ".join(get_color(value)))

        def get_indicator_for_datetime(dt: datetime) -> int:
            total_seconds = (now - dt).total_seconds()

            MAX_SECONDS = 10

            return 100 - int(max(0.0, min(total_seconds, MAX_SECONDS) / MAX_SECONDS * 100))

        content = render_template_string(
            """
            <style>
                body {
                    font-family: sans-serif;
                    background-color: #f5f5f5;
                }

                .tasks_grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    grid-gap: 20px;
                    padding: 0;
                    list-style: none;
                }

                .tasks_grid_item {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 5px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }

                .task_info {
                    margin-bottom: 20px;
                }

                .task_name {
                    margin: 0;
                    font-size: 1.5rem;
                }

                .task_cron {
                    margin: 0;
                    font-size: 1rem;
                    color: #666;
                }

                .task_next_run {
                    margin: 0;
                    font-size: 1rem;
                    color: #666;
                }

                .task_actions {
                    display: flex;
                    justify-content: flex-end;
                }

                .task_action_button {
                    padding: 10px 20px;
                    border: 0;
                    border-radius: 5px;
                    background-color: #fff;
                    
                    font-size: 1rem;
                    font-weight: bold;
                    color: #666;
                    cursor: pointer;
                }

                .task_action_button:hover {
                    background-color: #f5f5f5;
                }

                .task_action_button:active {
                    background-color: #eee;
                }

                .task_action_button + .task_action_button {
                    margin-left: 10px;
                }

                .app_info {
                    margin-bottom: 20px;
                }

                .app_info h1 {
                    margin: 0;
                    font-size: 2rem;
                }

                .app_info h4 {
                    margin: 0;
                    font-size: 1rem;
                    color: #666;
                }

                .app_info h4 + h4 {
                    margin-top: 10px;
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    grid-gap: 10px;
                }

                

                
            </style>
            <div class="app_info">
                <h1>App info</h1>
                <h4>Now: {{ now }}</h4>
                <h4>App started at: {{ app_started_at }}</h4>
                <h4>Next check time: {{ next_check_time }}</h4>
                <h4>Remaining seconds to next check: {{ remaining_seconds_to_next_check }}</h4>
            </div>
            <h1>Tasks</h1>
            <ul class="tasks_grid">
                {% for task_name, task in tasks.items() %}
                    <li 
                        class="tasks_grid_item"
                        style="background-color: {{ get_rgb_background_color(get_indicator_for_datetime(tasks_last_run_getter(task_name))) if tasks_last_run_getter(task_name) else 'rgb(230, 230, 230)' }}"
                    >
                        <div class="task_info">
                            <h2 class="task_name">{{ task_name }}</h2>
                            <p class="task_cron">Cron: {{ task.cron }}</p>
                            <p class="task_cron">Last run at: {{ tasks_last_run_getter(task_name) or 'Never' }}</p>
                            <p class="task_next_run">Next run at: {{ task.next_run_at }}</p>
                        </div>
                        <div class="task_actions">
                            <button class="task_action_button">Run now</button>
                            <button class="task_action_button">Delete</button>
                        </div>
                    </li>
                {% endfor %}
            </ul>
            """,
            tasks={
                task_name: {
                    "next_run_at": get_next_run_at(
                        task.cron, info_provider.get_tasks_last_run_at(task_name) or now
                    ),
                    "cron": task.cron,
                }
                for task_name, task in info_provider.get_tasks().items()
            },
            tasks_last_run_getter=info_provider.get_tasks_last_run_at,
            now=now,
            app_started_at=info_provider.get_app_started_at(),
            next_check_time=info_provider.get_next_check_time(),
            remaining_seconds_to_next_check=remaining_seconds_to_next_check,
            get_indicator_for_datetime=get_indicator_for_datetime,
            get_rgb_background_color=get_rgb_background_color,
        )

        slitted_url = urlsplit(request.url)
        uri = urlunsplit(
            ("", "", slitted_url.path, slitted_url.query, slitted_url.fragment)
        )

        return Response(
            content,
            mimetype="text/html",
            headers={
                "Refresh": "{}; url={}".format(
                    request.args.get("refresh", 1),
                    uri,
                ),
            },
        )

    app.add_url_rule("/", "index", index, methods=("GET",))

    def add_task() -> Response:
        if request.method == "GET":
            random_task_name = "task_{}".format(
                "".join(
                    random.choice(string.ascii_lowercase + string.digits)
                    for _ in range(10)
                )
            )

            content = render_template_string(
                """
                <style>
                    body {
                        font-family: sans-serif;
                        background-color: #f5f5f5;
                    }

                    form {
                        max-width: 500px;
                        margin: 0 auto;
                    }

                    fieldset {
                        margin-bottom: 20px;
                    }

                    label {
                        display: block;
                        margin-bottom: 5px;
                    }

                    input {
                        display: block;
                        width: 100%;
                        padding: 10px;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        font-size: 1rem;
                    }

                    input[type="submit"] {
                        background-color: #fff;
                        cursor: pointer;
                    }

                    input[type="submit"]:hover {
                        background-color: #f5f5f5;
                    }

                    input[type="submit"]:active {
                        background-color: #eee;
                    }

                    input[type="checkbox"] {
                        width: auto;
                    }

                </style>

                

                <h1>Add task</h1>
                
                <form method="POST" class="add_task_form">
                    <fieldset>
                        <label for="task_name">Task name</label>
                        <input type="text" name="task_name" id="task_name" value="{{ random_task_name }}">
                    </fieldset>
                    <fieldset>
                        <label for="cron">Cron</label>
                        <input type="text" name="cron" id="cron" value="* * * * *">
                    </fieldset>
                    <fieldset>
                        <label for="immediate_first_run">Immediate first run</label>
                        <input type="checkbox" name="immediate_first_run" id="immediate_first_run">
                    </fieldset>
                    <input type="submit" value="Add task">
                </form>
                """,
                random_task_name=random_task_name,
            )
            return Response(content, mimetype="text/html")

        if request.method == "POST":
            # validate task name and cron

            if not request.form["task_name"]:
                return Response("Task name is required", status=400)

            if not request.form["cron"]:
                return Response("Cron is required", status=400)
            
            # tests cron
            try:
                croniter.croniter(request.form["cron"])
            except Exception:
                return Response("Invalid cron", status=400)
            

            if request.form["task_name"] in info_provider.get_tasks():
                return Response("Task already exists", status=400)

            # validate cron
            cron = request.form["cron"].split(" ")

            if len(cron) not in (5, 6) or not all(cron):
                return Response("Invalid cron", status=400)

            task_management_provider.insert_task(
                request.form["task_name"],
                PeriodicTrigger(
                    request.form["cron"],
                    bool(request.form.get("immediate_first_run")),
                ),
            )

            return Response(
                "Task added",
                status=201,
                headers={"Refresh": "1; url=/add_task"},
            )

        return Response("Method not allowed", status=405)

    app.add_url_rule("/add_task", "add_task", add_task, methods=("GET", "POST"))

    return app
