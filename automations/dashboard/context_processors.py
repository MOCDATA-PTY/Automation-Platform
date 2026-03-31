STATIONS_NAV = [
    ('TRN', 'turnover', 'Turnover'),
    ('ATL', 'atl', 'ATL'),
    ('CCC', 'ccc', 'CCC'),
    ('CCD', 'ccd', 'CCD'),
    ('CON', 'con', 'CON'),
    ('DOR', 'dor', 'DOR'),
    ('FAX', 'fax', 'FAX'),
    ('HNL', 'hnl', 'HNL'),
    ('HOU', 'hou', 'HOU'),
    ('ICS', 'ics', 'ICS'),
    ('IMP', 'imp', 'IMP'),
    ('JFK', 'jfk', 'JFK'),
    ('LAX', 'lax', 'LAX'),
    ('LCL', 'lcl', 'LCL'),
    ('ORD', 'ord', 'ORD'),
    ('DFW', 'dfw', 'DFW'),
    ('PPG', 'ppg', 'PPG'),
    ('CDR', 'condor_dor', 'Condor+DOR'),
    ('IOP', 'import_ops', 'Import Ops'),
    ('WIP', 'wip_accrual', 'WIP & Accrual'),
    ('CRD', 'creditor', 'Creditor'),
]


def theme(request):
    dark_mode = False
    if request.user.is_authenticated:
        try:
            dark_mode = request.user.profile.dark_mode
        except Exception:
            pass
    return {'dark_mode': dark_mode, 'stations_nav': STATIONS_NAV}
