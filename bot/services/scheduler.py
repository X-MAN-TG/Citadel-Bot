import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Union

log = logging.getLogger(__name__)


class Job:
    def __init__(
        self,
        callback: Callable[..., Any],
        name: Optional[str] = None,
        data: Any = None,
        interval: Optional[float] = None,
    ):
        self.callback = callback
        self.name = name
        self.data = data
        self.interval = interval
        self.removed: bool = False
        self.task: Optional[asyncio.Task] = None

    def schedule_removal(self) -> None:
        self.removed = True
        if self.task and not self.task.done():
            self.task.cancel()


class JobContext:
    def __init__(
        self,
        bot: Any,
        bot_data: Dict[str, Any],
        job: Job,
        job_queue: "AsyncJobQueue",
    ):
        self.bot = bot
        self.bot_data = bot_data
        self.job = job
        self.job_queue = job_queue

    @property
    def data(self) -> Any:
        return self.job.data


class AsyncJobQueue:
    def __init__(self, bot: Any = None, bot_data: Optional[Dict[str, Any]] = None):
        self.bot = bot
        self.bot_data = bot_data if bot_data is not None else {}
        self._jobs: List[Job] = []
        self._tasks: List[asyncio.Task] = []
        self._running = False

    def set_bot(self, bot: Any, bot_data: Dict[str, Any]) -> None:
        self.bot = bot
        self.bot_data = bot_data
        self._running = True

    @staticmethod
    def _calc_delay(when: Union[int, float, timedelta, datetime]) -> float:
        if isinstance(when, (int, float)):
            return max(0.0, float(when))
        if isinstance(when, timedelta):
            return max(0.0, when.total_seconds())
        if isinstance(when, datetime):
            now = datetime.now(timezone.utc)
            if when.tzinfo is None:
                now = datetime.now()
            return max(0.0, (when - now).total_seconds())
        return 0.0

    async def _execute_job(self, job: Job) -> None:
        if job.removed:
            return
        ctx = JobContext(
            bot=self.bot,
            bot_data=self.bot_data,
            job=job,
            job_queue=self,
        )
        try:
            res = job.callback(ctx)
            if asyncio.iscoroutine(res):
                await res
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.exception("Error executing scheduled job %s: %s", job.name, e)

    async def _run_once_loop(self, job: Job, delay: float) -> None:
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            await self._execute_job(job)
        except asyncio.CancelledError:
            pass
        finally:
            job.removed = True
            if job in self._jobs:
                self._jobs.remove(job)

    async def _run_repeating_loop(self, job: Job, first_delay: float, interval: float) -> None:
        try:
            if first_delay > 0:
                await asyncio.sleep(first_delay)
            while not job.removed and self._running:
                await self._execute_job(job)
                if job.removed or not self._running:
                    break
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass
        finally:
            job.removed = True
            if job in self._jobs:
                self._jobs.remove(job)

    def run_once(
        self,
        callback: Callable[..., Any],
        when: Union[int, float, timedelta, datetime],
        data: Any = None,
        name: Optional[str] = None,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Job:
        delay = self._calc_delay(when)
        job = Job(callback=callback, name=name, data=data)
        task = asyncio.create_task(self._run_once_loop(job, delay))
        job.task = task
        self._jobs.append(job)
        self._tasks.append(task)
        return job

    def run_repeating(
        self,
        callback: Callable[..., Any],
        interval: Union[int, float, timedelta],
        first: Optional[Union[int, float, timedelta, datetime]] = None,
        data: Any = None,
        name: Optional[str] = None,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> Job:
        int_secs = interval.total_seconds() if isinstance(interval, timedelta) else float(interval)
        first_delay = self._calc_delay(first) if first is not None else int_secs
        job = Job(callback=callback, name=name, data=data, interval=int_secs)
        task = asyncio.create_task(self._run_repeating_loop(job, first_delay, int_secs))
        job.task = task
        self._jobs.append(job)
        self._tasks.append(task)
        return job

    def get_jobs_by_name(self, name: str) -> List[Job]:
        return [j for j in self._jobs if j.name == name and not j.removed]

    def stop(self) -> None:
        self._running = False
        for job in self._jobs:
            job.schedule_removal()
        self._jobs.clear()
        for task in self._tasks:
            if not task.done():
                task.cancel()
        self._tasks.clear()
