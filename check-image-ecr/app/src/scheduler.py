import os
import concurrent.futures
from typing import List, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

from .config_loader import ConfigLoader, ConfigEntry
from .ecr_client import ECRClient
from .k8s_client import K8sClient
from .file_updater import atomic_write
from .report import generate_json_report, generate_html_report, save_report
from .notifier import notify_email, notify_slack


logger = structlog.get_logger()


def check_and_update(entry: ConfigEntry, ecr: ECRClient, k8s: K8sClient) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "deployment": entry.deployment,
        "image": entry.image,
        "old_sha": entry.sha,
        "new_sha": None,
        "updated": False,
        "error": None,
    }
    try:
        new_sha = ecr.get_latest_digest(entry.image)
        result["new_sha"] = new_sha
        if not new_sha:
            result["error"] = "No digest found"
            return result
        if new_sha != entry.sha:
            ok = k8s.rollout_restart(entry.deployment)
            if ok:
                ready = k8s.wait_until_ready(entry.deployment)
                result["updated"] = ready
            else:
                result["error"] = "Rollout restart failed"
        return result
    except Exception as e:
        result["error"] = str(e)
        return result


def run_once(config_path: str = "/app/config.txt"):
    loader = ConfigLoader(config_path)
    entries = loader.read()
    if not entries:
        logger.warning("no_entries_to_check")
        return

    ecr = ECRClient()
    k8s = K8sClient(namespace=os.getenv("TARGET_NAMESPACE", "digigold"))

    max_workers = int(os.getenv("MAX_WORKERS", "4"))
    results: List[Dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {executor.submit(check_and_update, e, ecr, k8s): e for e in entries}
        for future in concurrent.futures.as_completed(future_to_entry):
            res = future.result()
            results.append(res)

    # Update config for changed SHAs
    changed = False
    updated_entries: List[ConfigEntry] = []
    for e in entries:
        match = next((r for r in results if r["deployment"] == e.deployment), None)
        if match and match.get("new_sha") and match.get("new_sha") != e.sha and match.get("updated"):
            updated_entries.append(ConfigEntry(deployment=e.deployment, image=e.image, sha=match["new_sha"]))
            changed = True
        else:
            updated_entries.append(e)

    if changed:
        lines = loader.format_lines(updated_entries)
        atomic_write(config_path, lines)
        logger.info("config_updated")

    # Report
    json_report = generate_json_report(results)
    save_report(json_report, name="report.json")
    html_report = generate_html_report(results)
    save_report(html_report, name="report.html")

    # Notify on errors
    errors = [r for r in results if r.get("error")]
    if errors:
        msg = f"Errors during ECR check: {errors}"
        notify_slack(msg)
        notify_email("ECR Check Errors", msg)


def setup_scheduler():
    cron_expr = os.getenv("CRON_SCHEDULE", "*/15 * * * *")
    scheduler = BackgroundScheduler()
    trigger = CronTrigger.from_crontab(cron_expr)
    scheduler.add_job(run_once, trigger, id="ecr_check_job", replace_existing=True)
    scheduler.start()
    logger.info("scheduler_started", cron=cron_expr)
    return scheduler