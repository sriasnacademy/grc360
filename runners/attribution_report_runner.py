"""
runners/attribution_report_runner.py
Exports the full attribution log to reports/attribution_log_<ts>.json
Can be triggered from the UI button, menu item, or scheduler.
"""
import json
import os
from datetime import datetime
from agents.attribution_agent import attribution_agent


class AttributionReportRunner:

    def run(self, output_dir: str = "reports") -> str:
        """Export the full log. Returns the saved file path."""
        os.makedirs(output_dir, exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"attribution_log_{ts}.json")
        data     = json.loads(attribution_agent.export_json())

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        n = len(data) if isinstance(data, list) else 1
        print(f"[AttributionReportRunner] {n} records → {filename}")
        return filename

    def print_summary(self):
        s = attribution_agent.summary()
        print("\n── Attribution Log Summary ──────────────────────────")
        print(f"  Total records : {s.get('total_records', 0)}")
        for k, v in s.get("by_action", {}).items():
            print(f"  {k:<34} {v}")
        print(f"  Earliest : {s.get('earliest', 'n/a')}")
        print(f"  Latest   : {s.get('latest',   'n/a')}")
        print("─────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    runner = AttributionReportRunner()
    runner.print_summary()
    path = runner.run()
    print("Saved →", path)
