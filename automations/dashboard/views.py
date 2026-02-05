from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db.models.functions import ExtractYear
from django.db import OperationalError, ProgrammingError, connection
from django.http import JsonResponse
from .models import TurnoverData
from .google_drive import sync_google_drive_data, get_progress, update_progress, get_last_sync
from . import onedrive_sync
import threading


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

    context = {
        'total_rows': total_rows,
        'branch_count': branch_count,
        'pnl_rows': pnl_rows,
        'pnl_divisions': pnl_divisions,
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
def sync_data(request):
    if request.method == 'POST':
        # Check if OneDrive is authenticated
        if not onedrive_sync.get_access_token():
            return JsonResponse({'status': 'error', 'message': 'OneDrive not connected'})

        update_progress('starting', 'Starting OneDrive sync...', 0, 100)

        def run_sync():
            try:
                update_progress('syncing', 'Syncing files from OneDrive...', 10, 100)
                count = onedrive_sync.sync_turnover_data()
                update_progress('complete', f'Synced {count} records', 100, 100)
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
