import subprocess
import winreg

hkcu = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
environment_key = winreg.OpenKey(hkcu, "Environment", access=winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
p = winreg.QueryValueEx(environment_key, "Path")[0].rstrip(';')
p += ";D:\\Code\\focus-time-app\\dist\\focus-time\\;"
print(p)

test = subprocess.run(["powershell", "-Command", f'[Environment]::SetEnvironmentVariable("PATH", "{p}", "USER")'], capture_output=True, check=True)
i = 2
# winreg.SetValueEx(environment_key, "Path", 0, winreg.REG_SZ, p)
