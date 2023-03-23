from dataclasses import dataclass
from datetime import datetime
from typing import Optional, cast

import croniter


@dataclass
class PeriodicTrigger:
    cron: str
    immediate_first_run: bool

    def can_run(self, now: datetime, last_run_at: datetime) -> bool:
        next_run_at = get_next_run_at(self.cron, last_run_at)
        print("{} <= {}".format(next_run_at, now))
        return next_run_at <= now


def get_next_run_at(cron: str, last_run_at: datetime) -> datetime:
    cron_iter = croniter.croniter(cron, last_run_at)
    return cast(datetime, cron_iter.get_next(datetime))
