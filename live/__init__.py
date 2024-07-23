import platform

OS = platform.system()
if OS == 'Linux' or OS == 'Darwin':
    pass
elif OS == 'Windows':
    from .parser import live_system_check
