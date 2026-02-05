from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

scheduler = None


def run_sync_job():
    """Run the OneDrive sync job"""
    from . import onedrive_sync
    from .views import update_progress
    try:
        logger.info("Starting scheduled OneDrive sync...")
        update_progress('running', 'Scheduled sync starting...', 0, 100)
        count = onedrive_sync.sync_turnover_data()
        logger.info(f"Scheduled sync complete: {count} records synced")
        update_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled sync error: {e}")
        update_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def start_scheduler():
    """Start the background scheduler"""
    global scheduler

    if scheduler is not None:
        return

    scheduler = BackgroundScheduler()

    # Run sync every hour
    scheduler.add_job(
        run_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='onedrive_sync',
        name='Sync OneDrive data every hour',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started - OneDrive syncing every hour")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
