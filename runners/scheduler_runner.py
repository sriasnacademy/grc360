import schedule
import time
from runners.manual_runner import ManualRunner

def start_scheduler(test_plan_id):
    runner = ManualRunner()

    schedule.every().day.at("01:00").do(
        runner.run,
        test_plan_id=test_plan_id
    )

    while True:
        schedule.run_pending()
        time.sleep(60)
