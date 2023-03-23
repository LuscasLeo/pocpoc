from dataclasses import dataclass
from threading import Thread
import time
from datetime import datetime, timedelta
from typing import Dict, NoReturn, Optional, Union

from example_2_scheduler.domain import PeriodicTrigger, get_next_run_at


class Sleeper:
    def __init__(self) -> None:
        self.__cancelled = False

    def cancel(self) -> None:
        self.__cancelled = True

    def sleep(self, sleep_time: Union[int, float]) -> None:
        count = 0
        while count < sleep_time:
            if self.__cancelled:
                break

            time.sleep(1)
            count += 1

    def reset(self) -> None:
        self.__cancelled = False


@dataclass
class AppData:
    sleeper: "Sleeper"
    tasks: Dict[str, PeriodicTrigger]
    tasks_last_run_at: Dict[str, datetime]
    tasks_last_run_check: Dict[str, Optional[datetime]]
    app_started_at: datetime
    app_next_check_time: Optional[datetime]


def start_webserver(app_data: AppData) -> None:
    from example_2_scheduler.presenter import create_app

    class AppInformationProvider:
        def get_tasks(self) -> Dict[str, PeriodicTrigger]:
            return app_data.tasks

        def get_tasks_last_run_at(self, task_name: str) -> Optional[datetime]:
            return app_data.tasks_last_run_at.get(task_name)

        def get_app_started_at(self) -> datetime:
            return app_data.app_started_at

        def get_next_check_time(self) -> Optional[datetime]:
            return app_data.app_next_check_time

    class TaskManagementProvider:
        def insert_task(self, task_name: str, task: PeriodicTrigger) -> None:
            app_data.tasks[task_name] = task

            app_data.sleeper.cancel()
            app_data.app_next_check_time = None

    app = create_app(
        info_provider=AppInformationProvider(),
        task_management_provider=TaskManagementProvider(),
    )

    app.run()


def main() -> NoReturn:
    APP_DEFAULT_SLEEP_TIME = 5

    app_data = AppData(
        app_started_at=datetime.now().replace(microsecond=0),
        app_next_check_time=None,
        # App goals: To be a scheduler that can run tasks periodically.
        # App workflow: The app sleeps until the next task is due to run, then runs it.
        # App requirements: The app must be able to run tasks at a given time, and must be able to run tasks immediately on startup.
        # Tasks Repository
        tasks={
            # Task 1: Run every 5 minutes, but run immediately on startup.
            # "task_1": PeriodicTrigger(cron="*/5 * * * *", immediate_first_run=True),
            # Task 2: Run every 10 minutes, but do not run immediately on startup.
            # "task_2": PeriodicTrigger(cron="*/10 * * * *", immediate_first_run=False),
        },
        # Tasks Last Run Dictionary
        tasks_last_run_at={},
        tasks_last_run_check={},
        sleeper=Sleeper(),
    )

    Thread(
        target=start_webserver,
        daemon=True,
        kwargs=dict(
            app_data=app_data,
        ),
    ).start()

    while True:
        app_data.sleeper.reset()
        now = datetime.now().replace(microsecond=0)
        next_sleep_time: Optional[float] = None

        for task_name, task in app_data.tasks.items():
            if (
                task.immediate_first_run
                and app_data.tasks_last_run_check.get(task_name) is None
                or task.can_run(
                    now,
                    app_data.tasks_last_run_at.get(task_name)
                    or app_data.app_started_at,
                )
            ):
                # Task Runner
                print(f"Running task {task_name}")

                # Task Last Run Updater
                app_data.tasks_last_run_at[task_name] = now

            if not task.immediate_first_run:
                app_data.tasks_last_run_check[task_name] = now

            # Task Next Run Time Calculator
            # Get the last run time for the task.
            task_last_run_at = app_data.tasks_last_run_at.get(task_name) or now

            task_next_run_at = get_next_run_at(task.cron, task_last_run_at)
            task_next_sleep_time = (task_next_run_at - now).total_seconds()

            if next_sleep_time is None or task_next_sleep_time < next_sleep_time:
                next_sleep_time = task_next_sleep_time
                app_data.app_next_check_time = task_next_run_at
        else:
            if next_sleep_time is None:
                next_sleep_time = APP_DEFAULT_SLEEP_TIME
                app_data.app_next_check_time = now + timedelta(seconds=next_sleep_time)

        final_sleep_time = next_sleep_time or APP_DEFAULT_SLEEP_TIME
        print(f"Sleeping for {final_sleep_time} seconds")
        app_data.sleeper.sleep(final_sleep_time)


if __name__ == "__main__":
    main()
