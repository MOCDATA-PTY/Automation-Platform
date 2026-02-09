from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

scheduler = None


def run_sync_job():
    """Run the OneDrive sync job for turnover data"""
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


def run_ppg_sync_job():
    """Run the PPG sync job"""
    from . import onedrive_sync
    from .views import update_ppg_progress
    try:
        logger.info("Starting scheduled PPG sync...")
        update_ppg_progress('running', 'Scheduled PPG sync starting...', 0, 100)
        count = onedrive_sync.sync_ppg_data()
        logger.info(f"Scheduled PPG sync complete: {count} records synced")
        update_ppg_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled PPG sync error: {e}")
        update_ppg_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_dor_sync_job():
    """Run the DOR sync job"""
    from . import onedrive_sync
    from .views import update_dor_progress
    try:
        logger.info("Starting scheduled DOR sync...")
        update_dor_progress('running', 'Scheduled DOR sync starting...', 0, 100)
        count = onedrive_sync.sync_dor_data()
        logger.info(f"Scheduled DOR sync complete: {count} records synced")
        update_dor_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled DOR sync error: {e}")
        update_dor_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_con_sync_job():
    """Run the CON sync job"""
    from . import onedrive_sync
    from .views import update_con_progress
    try:
        logger.info("Starting scheduled CON sync...")
        update_con_progress('running', 'Scheduled CON sync starting...', 0, 100)
        count = onedrive_sync.sync_con_data()
        logger.info(f"Scheduled CON sync complete: {count} records synced")
        update_con_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled CON sync error: {e}")
        update_con_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_ccd_sync_job():
    """Run the CCD sync job"""
    from . import onedrive_sync
    from .views import update_ccd_progress
    try:
        logger.info("Starting scheduled CCD sync...")
        update_ccd_progress('running', 'Scheduled CCD sync starting...', 0, 100)
        count = onedrive_sync.sync_ccd_data()
        logger.info(f"Scheduled CCD sync complete: {count} records synced")
        update_ccd_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled CCD sync error: {e}")
        update_ccd_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_atl_sync_job():
    """Run the ATL sync job"""
    from . import onedrive_sync
    from .views import update_atl_progress
    try:
        logger.info("Starting scheduled ATL sync...")
        update_atl_progress('running', 'Scheduled ATL sync starting...', 0, 100)
        count = onedrive_sync.sync_atl_data()
        logger.info(f"Scheduled ATL sync complete: {count} records synced")
        update_atl_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled ATL sync error: {e}")
        update_atl_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_ccc_sync_job():
    """Run the CCC sync job"""
    from . import onedrive_sync
    from .views import update_ccc_progress
    try:
        logger.info("Starting scheduled CCC sync...")
        update_ccc_progress('running', 'Scheduled CCC sync starting...', 0, 100)
        count = onedrive_sync.sync_ccc_data()
        logger.info(f"Scheduled CCC sync complete: {count} records synced")
        update_ccc_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled CCC sync error: {e}")
        update_ccc_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_hnl_sync_job():
    """Run the HNL sync job"""
    from . import onedrive_sync
    from .views import update_hnl_progress
    try:
        logger.info("Starting scheduled HNL sync...")
        update_hnl_progress('running', 'Scheduled HNL sync starting...', 0, 100)
        count = onedrive_sync.sync_hnl_data()
        logger.info(f"Scheduled HNL sync complete: {count} records synced")
        update_hnl_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled HNL sync error: {e}")
        update_hnl_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_jfk_sync_job():
    """Run the JFK sync job"""
    from . import onedrive_sync
    from .views import update_jfk_progress
    try:
        logger.info("Starting scheduled JFK sync...")
        update_jfk_progress('running', 'Scheduled JFK sync starting...', 0, 100)
        count = onedrive_sync.sync_jfk_data()
        logger.info(f"Scheduled JFK sync complete: {count} records synced")
        update_jfk_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled JFK sync error: {e}")
        update_jfk_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_fax_sync_job():
    """Run the FAX sync job"""
    from . import onedrive_sync
    from .views import update_fax_progress
    try:
        logger.info("Starting scheduled FAX sync...")
        update_fax_progress('running', 'Scheduled FAX sync starting...', 0, 100)
        count = onedrive_sync.sync_fax_data()
        logger.info(f"Scheduled FAX sync complete: {count} records synced")
        update_fax_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled FAX sync error: {e}")
        update_fax_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_hou_sync_job():
    """Run the HOU sync job"""
    from . import onedrive_sync
    from .views import update_hou_progress
    try:
        logger.info("Starting scheduled HOU sync...")
        update_hou_progress('running', 'Scheduled HOU sync starting...', 0, 100)
        count = onedrive_sync.sync_hou_data()
        logger.info(f"Scheduled HOU sync complete: {count} records synced")
        update_hou_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled HOU sync error: {e}")
        update_hou_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_ics_sync_job():
    """Run the ICS sync job"""
    from . import onedrive_sync
    from .views import update_ics_progress
    try:
        logger.info("Starting scheduled ICS sync...")
        update_ics_progress('running', 'Scheduled ICS sync starting...', 0, 100)
        count = onedrive_sync.sync_ics_data()
        logger.info(f"Scheduled ICS sync complete: {count} records synced")
        update_ics_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled ICS sync error: {e}")
        update_ics_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_imp_sync_job():
    """Run the IMP sync job"""
    from . import onedrive_sync
    from .views import update_imp_progress
    try:
        logger.info("Starting scheduled IMP sync...")
        update_imp_progress('running', 'Scheduled IMP sync starting...', 0, 100)
        count = onedrive_sync.sync_imp_data()
        logger.info(f"Scheduled IMP sync complete: {count} records synced")
        update_imp_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled IMP sync error: {e}")
        update_imp_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_lax_sync_job():
    """Run the LAX sync job"""
    from . import onedrive_sync
    from .views import update_lax_progress
    try:
        logger.info("Starting scheduled LAX sync...")
        update_lax_progress('running', 'Scheduled LAX sync starting...', 0, 100)
        count = onedrive_sync.sync_lax_data()
        logger.info(f"Scheduled LAX sync complete: {count} records synced")
        update_lax_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled LAX sync error: {e}")
        update_lax_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_lcl_sync_job():
    """Run the LCL sync job"""
    from . import onedrive_sync
    from .views import update_lcl_progress
    try:
        logger.info("Starting scheduled LCL sync...")
        update_lcl_progress('running', 'Scheduled LCL sync starting...', 0, 100)
        count = onedrive_sync.sync_lcl_data()
        logger.info(f"Scheduled LCL sync complete: {count} records synced")
        update_lcl_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled LCL sync error: {e}")
        update_lcl_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def run_ord_sync_job():
    """Run the ORD sync job"""
    from . import onedrive_sync
    from .views import update_ord_progress
    try:
        logger.info("Starting scheduled ORD sync...")
        update_ord_progress('running', 'Scheduled ORD sync starting...', 0, 100)
        count = onedrive_sync.sync_ord_data()
        logger.info(f"Scheduled ORD sync complete: {count} records synced")
        update_ord_progress('complete', f'Synced {count} records', 100, 100)
    except Exception as e:
        logger.error(f"Scheduled ORD sync error: {e}")
        update_ord_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)


def refresh_onedrive_token():
    """Refresh the OneDrive access token to keep it alive"""
    from . import onedrive_sync
    try:
        token = onedrive_sync.get_access_token()
        if token:
            logger.info("OneDrive token refreshed successfully")
        else:
            logger.warning("OneDrive token refresh returned None")
    except Exception as e:
        logger.error(f"OneDrive token refresh error: {e}")


def start_scheduler():
    """Start the background scheduler"""
    global scheduler

    if scheduler is not None:
        return

    scheduler = BackgroundScheduler()

    # Run turnover sync every hour
    scheduler.add_job(
        run_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='onedrive_sync',
        name='Sync OneDrive turnover data every hour',
        replace_existing=True
    )

    # Run PPG sync every hour
    scheduler.add_job(
        run_ppg_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='ppg_sync',
        name='Sync PPG data every hour',
        replace_existing=True
    )

    # Run DOR sync every hour
    scheduler.add_job(
        run_dor_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='dor_sync',
        name='Sync DOR data every hour',
        replace_existing=True
    )

    # Run CON sync every hour
    scheduler.add_job(
        run_con_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='con_sync',
        name='Sync CON data every hour',
        replace_existing=True
    )

    # Run CCD sync every hour
    scheduler.add_job(
        run_ccd_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='ccd_sync',
        name='Sync CCD data every hour',
        replace_existing=True
    )

    # Run ATL sync every hour
    scheduler.add_job(
        run_atl_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='atl_sync',
        name='Sync ATL data every hour',
        replace_existing=True
    )

    # Run CCC sync every hour
    scheduler.add_job(
        run_ccc_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='ccc_sync',
        name='Sync CCC data every hour',
        replace_existing=True
    )

    # Run HNL sync every hour
    scheduler.add_job(
        run_hnl_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='hnl_sync',
        name='Sync HNL data every hour',
        replace_existing=True
    )

    # Run JFK sync every hour
    scheduler.add_job(
        run_jfk_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='jfk_sync',
        name='Sync JFK data every hour',
        replace_existing=True
    )

    # Run FAX sync every hour
    scheduler.add_job(
        run_fax_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='fax_sync',
        name='Sync FAX data every hour',
        replace_existing=True
    )

    # Run HOU sync every hour
    scheduler.add_job(
        run_hou_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='hou_sync',
        name='Sync HOU data every hour',
        replace_existing=True
    )

    # Run ICS sync every hour
    scheduler.add_job(
        run_ics_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='ics_sync',
        name='Sync ICS data every hour',
        replace_existing=True
    )

    # Run IMP sync every hour
    scheduler.add_job(
        run_imp_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='imp_sync',
        name='Sync IMP data every hour',
        replace_existing=True
    )

    # Run LAX sync every hour
    scheduler.add_job(
        run_lax_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='lax_sync',
        name='Sync LAX data every hour',
        replace_existing=True
    )

    # Run LCL sync every hour
    scheduler.add_job(
        run_lcl_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='lcl_sync',
        name='Sync LCL data every hour',
        replace_existing=True
    )

    # Run ORD sync every hour
    scheduler.add_job(
        run_ord_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='ord_sync',
        name='Sync ORD data every hour',
        replace_existing=True
    )

    # Refresh OneDrive token every 10 minutes
    scheduler.add_job(
        refresh_onedrive_token,
        trigger=IntervalTrigger(minutes=10),
        id='token_refresh',
        name='Refresh OneDrive token every 10 minutes',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started - All stations syncing every hour, token refresh every 10 minutes")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
