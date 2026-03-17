from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
import json
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

scheduler = None


def update_sync_health(station, status, message, records=0):
    """Write sync health info for a station to sync_health.json"""
    import tempfile
    try:
        health_file = settings.SYNC_HEALTH_FILE
        health_data = {}
        if os.path.exists(health_file):
            try:
                with open(health_file, 'r') as f:
                    health_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                logger.warning(f"Corrupted sync_health.json, resetting")
                health_data = {}

        local_time = datetime.now(ZoneInfo('Africa/Johannesburg'))
        health_data[station] = {
            'last_check': local_time.isoformat(),
            'status': status,
            'message': message,
            'records': records,
        }

        # Atomic write to prevent corruption from concurrent workers
        dir_name = os.path.dirname(health_file)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(health_data, f, indent=2)
            os.replace(tmp_path, health_file)
        except Exception:
            os.unlink(tmp_path)
            raise
    except Exception as e:
        logger.error(f"Failed to update sync health for {station}: {e}")


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
        update_sync_health('turnover', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled sync error: {e}")
        update_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('turnover', 'error', str(e))


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
        update_sync_health('ppg', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled PPG sync error: {e}")
        update_ppg_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('ppg', 'error', str(e))


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
        update_sync_health('dor', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled DOR sync error: {e}")
        update_dor_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('dor', 'error', str(e))


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
        update_sync_health('con', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled CON sync error: {e}")
        update_con_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('con', 'error', str(e))


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
        update_sync_health('ccd', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled CCD sync error: {e}")
        update_ccd_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('ccd', 'error', str(e))


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
        update_sync_health('atl', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled ATL sync error: {e}")
        update_atl_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('atl', 'error', str(e))


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
        update_sync_health('ccc', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled CCC sync error: {e}")
        update_ccc_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('ccc', 'error', str(e))


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
        update_sync_health('hnl', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled HNL sync error: {e}")
        update_hnl_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('hnl', 'error', str(e))


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
        update_sync_health('jfk', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled JFK sync error: {e}")
        update_jfk_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('jfk', 'error', str(e))


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
        update_sync_health('fax', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled FAX sync error: {e}")
        update_fax_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('fax', 'error', str(e))


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
        update_sync_health('hou', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled HOU sync error: {e}")
        update_hou_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('hou', 'error', str(e))


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
        update_sync_health('ics', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled ICS sync error: {e}")
        update_ics_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('ics', 'error', str(e))


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
        update_sync_health('imp', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled IMP sync error: {e}")
        update_imp_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('imp', 'error', str(e))


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
        update_sync_health('lax', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled LAX sync error: {e}")
        update_lax_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('lax', 'error', str(e))


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
        update_sync_health('lcl', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled LCL sync error: {e}")
        update_lcl_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('lcl', 'error', str(e))


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
        update_sync_health('ord', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled ORD sync error: {e}")
        update_ord_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('ord', 'error', str(e))


def run_dfw_sync_job():
    """Run the DFW sync job"""
    from . import onedrive_sync
    from .views import update_dfw_progress
    try:
        logger.info("Starting scheduled DFW sync...")
        update_dfw_progress('running', 'Scheduled DFW sync starting...', 0, 100)
        count = onedrive_sync.sync_dfw_data()
        logger.info(f"Scheduled DFW sync complete: {count} records synced")
        update_dfw_progress('complete', f'Synced {count} records', 100, 100)
        update_sync_health('dfw', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled DFW sync error: {e}")
        update_dfw_progress('error', f'Scheduled sync error: {str(e)}', 0, 100)
        update_sync_health('dfw', 'error', str(e))


def run_creditor_sync_job():
    """Run the Creditor sync job"""
    from . import onedrive_sync
    try:
        logger.info("Starting scheduled Creditor sync...")
        count = onedrive_sync.sync_creditor_data()
        logger.info(f"Scheduled Creditor sync complete: {count} records synced")
        update_sync_health('creditor', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled Creditor sync error: {e}")
        update_sync_health('creditor', 'error', str(e))


def run_condor_dor_sync_job():
    """Run the Condor+DOR PNL sync job"""
    from . import onedrive_sync
    try:
        logger.info("Starting scheduled Condor+DOR sync...")
        count = onedrive_sync.sync_condor_dor_data()
        logger.info(f"Scheduled Condor+DOR sync complete: {count} records synced")
        update_sync_health('condor_dor', 'success', f'No file' if count == 0 else f'Synced {count} records', count)
    except Exception as e:
        logger.error(f"Scheduled Condor+DOR sync error: {e}")
        update_sync_health('condor_dor', 'error', str(e))


def refresh_onedrive_token():
    """Refresh the OneDrive access token to keep it alive.

    The actual retry logic lives in get_access_token() which retries 3 times
    with backoff. This function tracks the result in sync health so the
    monitoring dashboard shows token status.
    """
    from . import onedrive_sync
    try:
        token = onedrive_sync.get_access_token()
        if token:
            logger.info("OneDrive token refreshed successfully")
            update_sync_health('onedrive_token', 'success', 'Token is active')
        else:
            logger.error("OneDrive token refresh returned None - all retries exhausted")
            update_sync_health('onedrive_token', 'error', 'Token refresh failed - re-authentication may be required')
    except Exception as e:
        logger.error(f"OneDrive token refresh error: {e}")
        update_sync_health('onedrive_token', 'error', f'Token refresh exception: {e}')


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

    # Run DFW sync every hour
    scheduler.add_job(
        run_dfw_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='dfw_sync',
        name='Sync DFW data every hour',
        replace_existing=True
    )

    # Run Creditor sync every hour
    scheduler.add_job(
        run_creditor_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='creditor_sync',
        name='Sync Creditor data every hour',
        replace_existing=True
    )

    # Run Condor+DOR PNL sync every hour
    scheduler.add_job(
        run_condor_dor_sync_job,
        trigger=IntervalTrigger(hours=1),
        id='condor_dor_sync',
        name='Sync Condor+DOR PNL data every hour',
        replace_existing=True
    )

    # Refresh OneDrive token every minute to ensure it never expires
    scheduler.add_job(
        refresh_onedrive_token,
        trigger=IntervalTrigger(minutes=1),
        id='token_refresh',
        name='Refresh OneDrive token every minute',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started - All stations syncing every hour, token refresh every minute")

    # Immediately refresh token on startup
    try:
        refresh_onedrive_token()
        logger.info("OneDrive token refreshed on startup")
    except Exception as e:
        logger.error(f"OneDrive token refresh on startup failed: {e}")


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None
