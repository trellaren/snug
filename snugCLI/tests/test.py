import GPUtil
import platform

GPUtil.showUtilization()

def system_info():
    system = platform.system()
    node = platform.node()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    processor = platform.processor()
    return system, node, release, version, machine, processor

sys_inf = system_info()
print(sys_inf)