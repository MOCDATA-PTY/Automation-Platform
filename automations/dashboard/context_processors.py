def theme(request):
    dark_mode = False
    if request.user.is_authenticated:
        try:
            dark_mode = request.user.profile.dark_mode
        except Exception:
            pass
    return {'dark_mode': dark_mode}
