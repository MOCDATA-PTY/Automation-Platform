from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import ExtractYear
from django.db import OperationalError, ProgrammingError, connection
from django.http import JsonResponse
from django.conf import settings as django_settings
from .models import TurnoverData, ProjectTask
from .google_drive import sync_google_drive_data, get_progress, update_progress, get_last_sync
from . import onedrive_sync
import threading
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            error = 'Invalid username or password'

    return render(request, 'login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    """Dashboard home page with project cards"""
    try:
        total_rows = TurnoverData.objects.count()
        branch_count = TurnoverData.objects.values('branch').distinct().count()
    except (OperationalError, ProgrammingError):
        total_rows = 0
        branch_count = 0

    # PNL stats
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM pnl_data")
            pnl_rows = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT division) FROM pnl_data")
            pnl_divisions = cursor.fetchone()[0]
    except:
        pnl_rows = 0
        pnl_divisions = 0

    # PNL station stats
    station_tables = {
        'ppg': 'ppg_pnl', 'dor': 'dor_pnl', 'con': 'con_pnl',
        'atl': 'atl_pnl', 'ccc': 'ccc_pnl', 'ccd': 'ccd_pnl',
        'fax': 'fax_pnl', 'hnl': 'hnl_pnl', 'hou': 'hou_pnl',
        'ics': 'ics_pnl', 'imp': 'imp_pnl', 'jfk': 'jfk_pnl',
        'lax': 'lax_pnl', 'lcl': 'lcl_pnl', 'ord': 'ord_pnl',
    }
    station_rows = {}
    for key, table in station_tables.items():
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                station_rows[f'{key}_rows'] = cursor.fetchone()[0]
        except:
            station_rows[f'{key}_rows'] = 0

    # Creditor stats
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM creditor_transactions")
            creditor_rows = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT creditor_group) FROM creditor_transactions")
            creditor_groups = cursor.fetchone()[0]
    except:
        creditor_rows = 0
        creditor_groups = 0

    # Condor+DOR stats
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM condor_dor_pnl")
            condor_rows = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT department) FROM condor_dor_pnl")
            condor_depts = cursor.fetchone()[0]
    except:
        condor_rows = 0
        condor_depts = 0

    planner_total = ProjectTask.objects.count()
    planner_in_progress = ProjectTask.objects.filter(status='in_progress').count()

    context = {
        'total_rows': total_rows,
        'branch_count': branch_count,
        'pnl_rows': pnl_rows,
        'pnl_divisions': pnl_divisions,
        'creditor_rows': creditor_rows,
        'creditor_groups': creditor_groups,
        'condor_rows': condor_rows,
        'condor_depts': condor_depts,
        'planner_total': planner_total,
        'planner_in_progress': planner_in_progress,
        **station_rows,
    }
    return render(request, 'home.html', context)


@login_required
def turnover(request):
    """Turnover Automation project page"""
    try:
        total_records = TurnoverData.objects.count()
        total_value = TurnoverData.objects.aggregate(total=Sum('value'))['total'] or 0
        branches = list(TurnoverData.objects.values_list('branch', flat=True).distinct())
        year_count = TurnoverData.objects.annotate(
            year=ExtractYear('date')
        ).values('year').distinct().count()
    except (OperationalError, ProgrammingError):
        total_records = 0
        total_value = 0
        branches = []
        year_count = 0

    context = {
        'total_records': total_records,
        'total_value': total_value,
        'branches': branches,
        'year_count': year_count,
        'last_sync': get_last_sync(),
    }
    return render(request, 'turnover.html', context)


@login_required
def pnl(request):
    """PNL Automation project page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM pnl_data")
            total_records = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT division) FROM pnl_data")
            division_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT date) FROM pnl_data")
            period_count = cursor.fetchone()[0]
            cursor.execute("SELECT DISTINCT division FROM pnl_data ORDER BY division")
            divisions = [row[0] for row in cursor.fetchall()]
    except:
        total_records = 0
        division_count = 0
        period_count = 0
        divisions = []

    context = {
        'total_records': total_records,
        'division_count': division_count,
        'period_count': period_count,
        'divisions': divisions,
    }
    return render(request, 'pnl.html', context)


@login_required
def ppg(request):
    """PPG Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ppg_pnl")
            total_records = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ppg_pnl WHERE budget_actual = 'Budget'")
            budget_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ppg_pnl WHERE budget_actual = 'Actual'")
            actual_count = cursor.fetchone()[0]
            cursor.execute("SELECT MIN(date), MAX(date) FROM ppg_pnl")
            min_date, max_date = cursor.fetchone()
    except:
        total_records = 0
        budget_count = 0
        actual_count = 0
        min_date = None
        max_date = None

    context = {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'min_date': min_date,
        'max_date': max_date,
        'last_sync': onedrive_sync.get_ppg_last_sync(),
    }
    return render(request, 'ppg.html', context)


@login_required
def sync_data(request):
    if request.method == 'POST':
        # Check if OneDrive is authenticated
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_progress('starting', 'Starting OneDrive sync...', 0, 100)

        def run_sync():
            try:
                update_progress('syncing', 'Checking OneDrive for new files...', 10, 100)
                count = onedrive_sync.sync_turnover_data()
                if count > 0:
                    update_progress('complete', f'Synced {count} new records', 100, 100)
                else:
                    update_progress('complete', 'No new files to sync — all up to date', 100, 100)
            except Exception as e:
                update_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started'})
    return redirect('turnover')


@login_required
def sync_progress(request):
    return JsonResponse(get_progress())


@login_required
def onedrive_auth(request):
    """Redirect to OneDrive authorization"""
    auth_url = onedrive_sync.get_auth_url()
    return redirect(auth_url)


@login_required
def onedrive_callback(request):
    """Handle OneDrive OAuth callback"""
    code = request.GET.get('code')
    if code:
        token = onedrive_sync.acquire_token_by_auth_code(code)
        if token:
            messages.success(request, 'OneDrive connected successfully!')
        else:
            messages.error(request, 'Failed to connect to OneDrive')
    return redirect('turnover')


@login_required
def onedrive_check(request):
    """Check if OneDrive is authenticated"""
    token = onedrive_sync.get_access_token()
    return JsonResponse({'authenticated': token is not None})


# PPG sync progress storage
ppg_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_ppg_progress(status, message, current=0, total=0):
    global ppg_sync_progress
    ppg_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_ppg(request):
    """Sync PPG data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_ppg_progress('starting', 'Starting PPG sync...', 0, 100)

        def run_sync():
            try:
                update_ppg_progress('syncing', 'Checking OneDrive for PPG files...', 10, 100)
                count = onedrive_sync.sync_ppg_data()
                if count > 0:
                    update_ppg_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_ppg_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_ppg_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started'})
    return redirect('ppg')


@login_required
def sync_ppg_progress(request):
    """Get PPG sync progress"""
    return JsonResponse(ppg_sync_progress)


# DOR views and sync
@login_required
def dor(request):
    """DOR Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM dor_pnl")
            total_records = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM dor_pnl WHERE budget_actual = 'Budget'")
            budget_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM dor_pnl WHERE budget_actual = 'Actual'")
            actual_count = cursor.fetchone()[0]
            cursor.execute("SELECT MIN(date), MAX(date) FROM dor_pnl")
            min_date, max_date = cursor.fetchone()
    except:
        total_records = 0
        budget_count = 0
        actual_count = 0
        min_date = None
        max_date = None

    context = {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'min_date': min_date,
        'max_date': max_date,
        'last_sync': onedrive_sync.get_dor_last_sync(),
    }
    return render(request, 'dor.html', context)


# DOR sync progress storage
dor_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_dor_progress(status, message, current=0, total=0):
    global dor_sync_progress
    dor_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_dor(request):
    """Sync DOR data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_dor_progress('starting', 'Starting DOR sync...', 0, 100)

        def run_sync():
            try:
                update_dor_progress('syncing', 'Checking OneDrive for DOR files...', 10, 100)
                count = onedrive_sync.sync_dor_data()
                if count > 0:
                    update_dor_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_dor_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_dor_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started'})
    return redirect('dor')


@login_required
def sync_dor_progress(request):
    """Get DOR sync progress"""
    return JsonResponse(dor_sync_progress)


# CON Views
con_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}
atl_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_con_progress(status, message, current=0, total=0):
    global con_sync_progress
    con_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


def update_atl_progress(status, message, current=0, total=0):
    global atl_sync_progress
    atl_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_con(request):
    """Sync CON data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_con_progress('starting', 'Starting CON sync...', 0, 100)

        def run_sync():
            try:
                update_con_progress('syncing', 'Checking OneDrive for CON files...', 10, 100)
                count = onedrive_sync.sync_con_data()
                if count > 0:
                    update_con_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_con_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_con_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started'})
    return redirect('con')


@login_required
def sync_con_progress(request):
    """Get CON sync progress"""
    return JsonResponse(con_sync_progress)


@login_required
def con(request):
    """CON Financial Analysis page"""
    with connection.cursor() as cursor:
        # Get total records
        cursor.execute("SELECT COUNT(*) FROM con_pnl")
        total_records = cursor.fetchone()[0] or 0

        # Get distinct months
        cursor.execute("SELECT COUNT(DISTINCT date) FROM con_pnl")
        month_count = cursor.fetchone()[0] or 0

        # Get distinct accounts
        cursor.execute("SELECT COUNT(DISTINCT account_name) FROM con_pnl")
        account_count = cursor.fetchone()[0] or 0

    last_sync = onedrive_sync.get_con_last_sync()

    return render(request, 'con.html', {
        'total_records': total_records,
        'month_count': month_count,
        'account_count': account_count,
        'last_sync': last_sync
    })

# ATL view
@login_required
def atl(request):
    """ATL Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM atl_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM atl_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM atl_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM atl_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0

    last_sync = onedrive_sync.get_atl_last_sync()

    return render(request, 'atl.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


@login_required
def sync_atl(request):
    """Sync ATL data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_atl_progress('starting', 'Starting ATL sync...', 0, 100)

        def run_sync():
            try:
                update_atl_progress('syncing', 'Checking OneDrive for ATL files...', 10, 100)
                count = onedrive_sync.sync_atl_data()
                if count > 0:
                    update_atl_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_atl_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_atl_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_atl_progress(request):
    """Get ATL sync progress"""
    return JsonResponse(atl_sync_progress)


# HNL views
@login_required
def hnl(request):
    """HNL Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM hnl_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM hnl_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM hnl_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM hnl_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0

    last_sync = onedrive_sync.get_hnl_last_sync()

    return render(request, 'hnl.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# HNL sync progress tracking
hnl_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_hnl_progress(status, message, current=0, total=0):
    global hnl_sync_progress
    hnl_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_hnl(request):
    """Sync HNL data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_hnl_progress('starting', 'Starting HNL sync...', 0, 100)

        def run_sync():
            try:
                update_hnl_progress('syncing', 'Checking OneDrive for HNL files...', 10, 100)
                count = onedrive_sync.sync_hnl_data()
                if count > 0:
                    update_hnl_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_hnl_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_hnl_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()
        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def sync_hnl_progress(request):
    """Get HNL sync progress"""
    return JsonResponse(hnl_sync_progress)


# CCC views
@login_required
def ccc(request):
    """CCC Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ccc_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM ccc_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM ccc_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM ccc_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0

    last_sync = onedrive_sync.get_ccc_last_sync()

    return render(request, 'ccc.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# CCC sync progress tracking
ccc_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_ccc_progress(status, message, current=0, total=0):
    global ccc_sync_progress
    ccc_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_ccc(request):
    """Sync CCC data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_ccc_progress('starting', 'Starting CCC sync...', 0, 100)

        def run_sync():
            try:
                update_ccc_progress('syncing', 'Checking OneDrive for CCC files...', 10, 100)
                count = onedrive_sync.sync_ccc_data()
                if count > 0:
                    update_ccc_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_ccc_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_ccc_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_ccc_progress(request):
    """Get CCC sync progress"""
    return JsonResponse(ccc_sync_progress)


# CCD view
@login_required
def ccd(request):
    """CCD Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ccd_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM ccd_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM ccd_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM ccd_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    last_sync = onedrive_sync.get_ccd_last_sync()

    return render(request, 'ccd.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# FAX view
@login_required
def fax(request):
    """FAX Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM fax_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM fax_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM fax_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM fax_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    last_sync = onedrive_sync.get_fax_last_sync()

    return render(request, 'fax.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# HEC view
@login_required
def hec(request):
    """HEC Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM pnl_data WHERE division = 'HEC'")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM pnl_data WHERE division = 'HEC' AND account_name LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM pnl_data WHERE division = 'HEC' AND account_name LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM pnl_data WHERE division = 'HEC'")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    return render(request, 'hec.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count
    })


# HOU view
@login_required
def hou(request):
    """HOU Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM hou_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM hou_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM hou_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM hou_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    last_sync = onedrive_sync.get_hou_last_sync()

    return render(request, 'hou.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# ICS view
@login_required
def ics(request):
    """ICS Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ics_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM ics_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM ics_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM ics_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    last_sync = onedrive_sync.get_ics_last_sync()

    return render(request, 'ics.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# IMP view
@login_required
def imp(request):
    """IMP Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM imp_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM imp_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM imp_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM imp_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    last_sync = onedrive_sync.get_imp_last_sync()

    return render(request, 'imp.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# JFK view
@login_required
def jfk(request):
    """JFK Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM jfk_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM jfk_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM jfk_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM jfk_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    last_sync = onedrive_sync.get_jfk_last_sync()

    return render(request, 'jfk.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# LAX view
@login_required
def lax(request):
    """LAX Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM lax_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM lax_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM lax_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM lax_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    last_sync = onedrive_sync.get_lax_last_sync()

    return render(request, 'lax.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# LCL view
@login_required
def lcl(request):
    """LCL Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM lcl_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM lcl_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM lcl_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM lcl_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    last_sync = onedrive_sync.get_lcl_last_sync()

    return render(request, 'lcl.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# ORD view
@login_required
def ord(request):
    """ORD Financial Analysis page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM ord_pnl")
            total_records = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM ord_pnl WHERE budget_actual LIKE '%Budget%'")
            budget_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM ord_pnl WHERE budget_actual LIKE '%Actual%'")
            actual_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM ord_pnl")
            account_count = cursor.fetchone()[0] or 0
    except:
        total_records = budget_count = actual_count = account_count = 0
    
    last_sync = onedrive_sync.get_ord_last_sync()

    return render(request, 'ord.html', {
        'total_records': total_records,
        'budget_count': budget_count,
        'actual_count': actual_count,
        'account_count': account_count,
        'last_sync': last_sync
    })


# CCD sync progress tracking
ccd_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_ccd_progress(status, message, current=0, total=0):
    global ccd_sync_progress
    ccd_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_ccd(request):
    """Sync CCD data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_ccd_progress('starting', 'Starting CCD sync...', 0, 100)

        def run_sync():
            try:
                update_ccd_progress('syncing', 'Checking OneDrive for CCD files...', 10, 100)
                count = onedrive_sync.sync_ccd_data()
                if count > 0:
                    update_ccd_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_ccd_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_ccd_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_ccd_progress(request):
    """Get CCD sync progress"""
    return JsonResponse(ccd_sync_progress)


# FAX sync progress tracking
fax_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_fax_progress(status, message, current=0, total=0):
    global fax_sync_progress
    fax_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_fax(request):
    """Sync FAX data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_fax_progress('starting', 'Starting FAX sync...', 0, 100)

        def run_sync():
            try:
                update_fax_progress('syncing', 'Checking OneDrive for FAX files...', 10, 100)
                count = onedrive_sync.sync_fax_data()
                if count > 0:
                    update_fax_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_fax_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_fax_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_fax_progress(request):
    """Get FAX sync progress"""
    return JsonResponse(fax_sync_progress)


# HOU sync progress tracking
hou_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_hou_progress(status, message, current=0, total=0):
    global hou_sync_progress
    hou_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_hou(request):
    """Sync HOU data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_hou_progress('starting', 'Starting HOU sync...', 0, 100)

        def run_sync():
            try:
                update_hou_progress('syncing', 'Checking OneDrive for HOU files...', 10, 100)
                count = onedrive_sync.sync_hou_data()
                if count > 0:
                    update_hou_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_hou_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_hou_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_hou_progress(request):
    """Get HOU sync progress"""
    return JsonResponse(hou_sync_progress)


# ICS sync progress tracking
ics_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_ics_progress(status, message, current=0, total=0):
    global ics_sync_progress
    ics_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_ics(request):
    """Sync ICS data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_ics_progress('starting', 'Starting ICS sync...', 0, 100)

        def run_sync():
            try:
                update_ics_progress('syncing', 'Checking OneDrive for ICS files...', 10, 100)
                count = onedrive_sync.sync_ics_data()
                if count > 0:
                    update_ics_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_ics_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_ics_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_ics_progress(request):
    """Get ICS sync progress"""
    return JsonResponse(ics_sync_progress)


# IMP sync progress tracking
imp_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_imp_progress(status, message, current=0, total=0):
    global imp_sync_progress
    imp_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_imp(request):
    """Sync IMP data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_imp_progress('starting', 'Starting IMP sync...', 0, 100)

        def run_sync():
            try:
                update_imp_progress('syncing', 'Checking OneDrive for IMP files...', 10, 100)
                count = onedrive_sync.sync_imp_data()
                if count > 0:
                    update_imp_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_imp_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_imp_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_imp_progress(request):
    """Get IMP sync progress"""
    return JsonResponse(imp_sync_progress)


# JFK sync progress tracking
jfk_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_jfk_progress(status, message, current=0, total=0):
    global jfk_sync_progress
    jfk_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_jfk(request):
    """Sync JFK data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_jfk_progress('starting', 'Starting JFK sync...', 0, 100)

        def run_sync():
            try:
                update_jfk_progress('syncing', 'Checking OneDrive for JFK files...', 10, 100)
                count = onedrive_sync.sync_jfk_data()
                if count > 0:
                    update_jfk_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_jfk_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_jfk_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_jfk_progress(request):
    """Get JFK sync progress"""
    return JsonResponse(jfk_sync_progress)


# LAX sync progress tracking
lax_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_lax_progress(status, message, current=0, total=0):
    global lax_sync_progress
    lax_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_lax(request):
    """Sync LAX data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_lax_progress('starting', 'Starting LAX sync...', 0, 100)

        def run_sync():
            try:
                update_lax_progress('syncing', 'Checking OneDrive for LAX files...', 10, 100)
                count = onedrive_sync.sync_lax_data()
                if count > 0:
                    update_lax_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_lax_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_lax_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_lax_progress(request):
    """Get LAX sync progress"""
    return JsonResponse(lax_sync_progress)


# LCL sync progress tracking
lcl_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_lcl_progress(status, message, current=0, total=0):
    global lcl_sync_progress
    lcl_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_lcl(request):
    """Sync LCL data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_lcl_progress('starting', 'Starting LCL sync...', 0, 100)

        def run_sync():
            try:
                update_lcl_progress('syncing', 'Checking OneDrive for LCL files...', 10, 100)
                count = onedrive_sync.sync_lcl_data()
                if count > 0:
                    update_lcl_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_lcl_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_lcl_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_lcl_progress(request):
    """Get LCL sync progress"""
    return JsonResponse(lcl_sync_progress)


# ORD sync progress tracking
ord_sync_progress = {'status': 'idle', 'message': '', 'current': 0, 'total': 0}


def update_ord_progress(status, message, current=0, total=0):
    global ord_sync_progress
    ord_sync_progress = {
        'status': status,
        'message': message,
        'current': current,
        'total': total
    }


@login_required
def sync_ord(request):
    """Sync ORD data from OneDrive"""
    if request.method == 'POST':
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_ord_progress('starting', 'Starting ORD sync...', 0, 100)

        def run_sync():
            try:
                update_ord_progress('syncing', 'Checking OneDrive for ORD files...', 10, 100)
                count = onedrive_sync.sync_ord_data()
                if count > 0:
                    update_ord_progress('complete', f'Synced {count} records', 100, 100)
                else:
                    update_ord_progress('complete', 'No files to sync', 100, 100)
            except Exception as e:
                update_ord_progress('error', f'Error: {str(e)}', 0, 100)

        thread = threading.Thread(target=run_sync)
        thread.start()

        return JsonResponse({'status': 'started', 'message': 'Sync started'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def sync_ord_progress(request):
    """Get ORD sync progress"""
    return JsonResponse(ord_sync_progress)


@login_required
def creditor(request):
    """Creditor Transaction Report page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM creditor_transactions")
            total_records = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT creditor) FROM creditor_transactions")
            creditor_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT creditor_group) FROM creditor_transactions")
            group_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT branch) FROM creditor_transactions WHERE branch != ''")
            branch_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT period) FROM creditor_transactions")
            period_count = cursor.fetchone()[0]
    except:
        total_records = 0
        creditor_count = 0
        group_count = 0
        branch_count = 0
        period_count = 0

    context = {
        'total_records': total_records,
        'creditor_count': creditor_count,
        'group_count': group_count,
        'branch_count': branch_count,
        'period_count': period_count,
    }
    return render(request, 'creditor.html', context)


@login_required
def condor_dor(request):
    """Condor+DOR PNL page"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM condor_dor_pnl")
            total_records = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT department) FROM condor_dor_pnl")
            dept_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT branch) FROM condor_dor_pnl")
            branch_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT account_name) FROM condor_dor_pnl")
            account_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(DISTINCT date) FROM condor_dor_pnl")
            period_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM condor_dor_pnl WHERE budget_actual = 'Budget'")
            budget_rows = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM condor_dor_pnl WHERE budget_actual = 'Actual'")
            actual_rows = cursor.fetchone()[0]
    except:
        total_records = 0
        dept_count = 0
        branch_count = 0
        account_count = 0
        period_count = 0
        budget_rows = 0
        actual_rows = 0

    context = {
        'total_records': total_records,
        'dept_count': dept_count,
        'branch_count': branch_count,
        'account_count': account_count,
        'period_count': period_count,
        'budget_rows': budget_rows,
        'actual_rows': actual_rows,
    }
    return render(request, 'condor_dor.html', context)


# --- Sync Monitor ---

STATIONS = [
    'turnover', 'creditor', 'condor_dor',
    'atl', 'ccc', 'ccd', 'con', 'dor', 'fax',
    'hnl', 'hou', 'ics', 'imp', 'jfk', 'lax',
    'lcl', 'ord', 'ppg',
]

STATION_TABLES = {
    'turnover': 'turnover_data',
    'creditor': 'creditor_transactions',
    'condor_dor': 'condor_dor_pnl',
    'atl': 'atl_pnl', 'ccc': 'ccc_pnl', 'ccd': 'ccd_pnl',
    'con': 'con_pnl', 'dor': 'dor_pnl', 'fax': 'fax_pnl',
    'hnl': 'hnl_pnl', 'hou': 'hou_pnl', 'ics': 'ics_pnl',
    'imp': 'imp_pnl', 'jfk': 'jfk_pnl', 'lax': 'lax_pnl',
    'lcl': 'lcl_pnl', 'ord': 'ord_pnl', 'ppg': 'ppg_pnl',
}


def _get_station_statuses():
    """Build station status list for the monitor page."""
    now = datetime.now(ZoneInfo('Africa/Johannesburg'))
    one_hour_ago = now - timedelta(hours=1)

    # Load health data
    health_data = {}
    try:
        health_file = django_settings.SYNC_HEALTH_FILE
        if os.path.exists(health_file):
            with open(health_file, 'r') as f:
                health_data = json.load(f)
    except Exception:
        pass

    stations = []
    healthy_count = 0
    stale_count = 0
    error_count = 0

    for station in STATIONS:
        # Read last_sync timestamp
        sync_file = getattr(django_settings, f'{station.upper()}_LAST_SYNC_FILE', None)
        last_sync_dt = None
        last_sync_display = None
        synced_data = False  # True when an actual last_sync file was found

        if sync_file and os.path.exists(sync_file):
            try:
                with open(sync_file, 'r') as f:
                    data = json.load(f)
                if 'last_sync' in data:
                    last_sync_dt = datetime.fromisoformat(data['last_sync'])
                    last_sync_display = {
                        'time': last_sync_dt.strftime('%H:%M'),
                        'date': last_sync_dt.strftime('%b %d, %Y'),
                    }
                    # had_data=True means actual records were processed;
                    # False means the job ran but found no file to import
                    synced_data = data.get('had_data', True)
            except Exception:
                pass

        # Read health info
        health = health_data.get(station, {})
        health_status = health.get('status', 'unknown')

        # Fallback: if no last_sync file, use sync_health last_check so the
        # monitor shows when the job last ran (e.g. "No file" syncs like CCC)
        if last_sync_dt is None and health.get('last_check'):
            try:
                last_sync_dt = datetime.fromisoformat(health['last_check'])
                last_sync_display = {
                    'time': last_sync_dt.strftime('%H:%M'),
                    'date': last_sync_dt.strftime('%b %d, %Y'),
                }
            except Exception:
                pass

        # Query actual record count from DB
        records = None
        table = STATION_TABLES.get(station)
        if table:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    records = cursor.fetchone()[0]
            except Exception:
                records = None

        # Determine overall status
        if health_status == 'error':
            status = 'error'
            error_count += 1
        elif last_sync_dt is None:
            status = 'unknown'
            stale_count += 1
        elif last_sync_dt < one_hour_ago:
            status = 'stale'
            stale_count += 1
        else:
            status = 'healthy'
            healthy_count += 1

        # Build a meaningful message from available data
        if health_status == 'error':
            message = health.get('message', 'Sync error')
        elif not synced_data:
            message = 'No file in OneDrive'
        elif records is not None:
            message = f'Synced {records:,} records'
        else:
            message = 'OK'

        # Time ago string
        time_ago = None
        if last_sync_dt:
            delta = now - last_sync_dt
            minutes = int(delta.total_seconds() / 60)
            if minutes < 1:
                time_ago = 'Just now'
            elif minutes < 60:
                time_ago = f'{minutes}m ago'
            elif minutes < 1440:
                time_ago = f'{minutes // 60}h {minutes % 60}m ago'
            else:
                time_ago = f'{minutes // 1440}d ago'

        stations.append({
            'code': station.upper(),
            'code_lower': station,
            'last_sync': last_sync_display,
            'time_ago': time_ago,
            'status': status,
            'health_status': health_status,
            'message': message,
            'records': records,
        })

    return stations, healthy_count, stale_count, error_count


@login_required
def sync_monitor(request):
    """Sync Monitor page"""
    stations, healthy, stale, errors = _get_station_statuses()
    context = {
        'stations': stations,
        'healthy_count': healthy,
        'stale_count': stale,
        'error_count': errors,
        'total_stations': len(STATIONS),
    }
    return render(request, 'monitor.html', context)


@login_required
def sync_monitor_api(request):
    """JSON API for auto-refresh of monitor data"""
    stations, healthy, stale, errors = _get_station_statuses()
    return JsonResponse({
        'stations': stations,
        'healthy_count': healthy,
        'stale_count': stale,
        'error_count': errors,
    })


@login_required
def sync_all(request):
    """Trigger a manual sync of all stations"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

    if not onedrive_sync.get_access_token():
        return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

    def run_all():
        from .scheduler import (
            run_sync_job, run_ppg_sync_job, run_dor_sync_job,
            run_con_sync_job, run_ccd_sync_job, run_atl_sync_job,
            run_ccc_sync_job, run_hnl_sync_job, run_jfk_sync_job,
            run_fax_sync_job, run_hou_sync_job, run_ics_sync_job,
            run_imp_sync_job, run_lax_sync_job, run_lcl_sync_job,
            run_ord_sync_job, run_creditor_sync_job, run_condor_dor_sync_job,
        )
        fns = [
            run_sync_job, run_ppg_sync_job, run_dor_sync_job,
            run_con_sync_job, run_ccd_sync_job, run_atl_sync_job,
            run_ccc_sync_job, run_hnl_sync_job, run_jfk_sync_job,
            run_fax_sync_job, run_hou_sync_job, run_ics_sync_job,
            run_imp_sync_job, run_lax_sync_job, run_lcl_sync_job,
            run_ord_sync_job, run_creditor_sync_job, run_condor_dor_sync_job,
        ]
        for fn in fns:
            threading.Thread(target=fn, daemon=True).start()

    threading.Thread(target=run_all, daemon=True).start()
    return JsonResponse({'status': 'started'})


# ── Project Planner ──────────────────────────────────────────────────────────

KANBAN_COLUMNS = [
    ('backlog',     'Backlog'),
    ('todo',        'To Do'),
    ('in_progress', 'In Progress'),
    ('review',      'Review'),
    ('done',        'Done'),
]


@login_required
def project_planner(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            ProjectTask.objects.create(
                title=title,
                description=request.POST.get('description', '').strip(),
                status=request.POST.get('status', 'backlog'),
                priority=request.POST.get('priority', 'medium'),
            )
        return JsonResponse({'status': 'ok'})

    columns = []
    for key, label in KANBAN_COLUMNS:
        tasks = list(ProjectTask.objects.filter(status=key).values(
            'id', 'title', 'description', 'priority', 'created_at'
        ))
        for t in tasks:
            t['created_at'] = t['created_at'].strftime('%b %d')
        columns.append({'key': key, 'label': label, 'tasks': tasks})

    total = ProjectTask.objects.count()
    in_progress = ProjectTask.objects.filter(status='in_progress').count()
    done = ProjectTask.objects.filter(status='done').count()

    return render(request, 'project_planner.html', {
        'columns': columns,
        'total': total,
        'in_progress': in_progress,
        'done': done,
    })


@login_required
def task_update(request, task_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    try:
        task = ProjectTask.objects.get(pk=task_id)
        data = json.loads(request.body)
        if 'status' in data:
            task.status = data['status']
        if 'title' in data:
            task.title = data['title'].strip() or task.title
        if 'description' in data:
            task.description = data['description'].strip()
        if 'priority' in data:
            task.priority = data['priority']
        task.save()
        return JsonResponse({'status': 'ok'})
    except ProjectTask.DoesNotExist:
        return JsonResponse({'status': 'not found'}, status=404)


@login_required
def task_delete(request, task_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)
    ProjectTask.objects.filter(pk=task_id).delete()
    return JsonResponse({'status': 'ok'})
