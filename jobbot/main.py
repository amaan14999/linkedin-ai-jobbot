import time
import schedule
from dotenv import load_dotenv

from jobbot.pipeline import run_cycle

load_dotenv()


def hourly_task() -> None:
    """
    Triggered by the scheduler every hour.
    It fetches jobs posted in the last 1 hour to find only the newest additions.
    """

    print("\n[Scheduler] Waking up! Starting the hourly job fetch...")

    try:
        run_cycle(hours=1)
        print("[Scheduler] Hourly cycle complete. Going back to sleep.")
    except Exception as e:
        print(f"[Scheduler] ERROR during hourly cycle: {e}")


def main() -> None:
    print("===================================================")
    print("  Initializing LinkedIn AI JobBot Daemon...        ")
    print("===================================================")

    print("\n[Init] Executing initial 24-hour fetch...")

    try:
        run_cycle(hours=24)
        pass
    except Exception as e:
        print(f"[Init] ERROR during initial cycle: {e}")

    schedule.every(1).hours.do(hourly_task)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
