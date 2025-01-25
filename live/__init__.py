import platform

OS = platform.system()
if OS == 'Linux' or OS == 'Darwin':
    def live_system_check():
        print("Linux and Mac environments aren't supported ")
    pass
elif OS == 'Windows':
    from .parser import live_system_check
