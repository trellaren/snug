from multiprocessing import process
import os
import wmi
import GPUtil
import psutil
import platform

def system_info():
    system = platform.system()
    node = platform.node()
    release = platform.release()
    version = platform.version()
    machine = platform.machine()
    processor = platform.processor()
    return system, node, release, version, machine, processor


def get_cpu_temps():
    ### CPU temps with psutil
    if hasattr(psutil, 'sensors_temperatures'):
        temps = psutil.sensors_temperatures()
        if temps:
            print("CPU Temperatures:")
            for name, entries in temps.items():
                for entry in entries:
                    print(f"- {entry.label or name}: {entry.current}°C")
        else:
            print("Temperature sensors not available on this system or no data")
    else:
        print("psutil version does not support sensors_temperatures or not supported on this OS")
    ### CPU temps from linux
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_milli = f.read().strip()
            temp_celsius = int(temp_milli) / 1000.0
            print(f"CPU Temperature: {temp_celsius}°C")
    except FileNotFoundError:
        print("Thermal information not found in /sys/class/thermal/thermal_zone0/temp")
    except Exception as e:
        print(f"An error occurred: {e}")

    # CPU Temps with OpenHardwareMonitor
    try:
        w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        temperature_info = w.Sensor()
        for sensor in temperature_info:
            if sensor.SensorType == u'Temperature':
                print(f"- {sensor.Name}: {sensor.Value}°C")
    except Exception as e:
        print(f"An error occurred, check if Open Hardware Monitor is running: {e}")

def get_gpu_temps():
    ### Nvidia Specific
    gpus = GPUtil.getGPUs()
    for gpu in gpus:
        print(f"GPU {gpu.id} ({gpu.name}): {gpu.temperature}°C")


def get_cpu_usage():
    return psutil.cpu_percent(), psutil.cpu_count(logical=False)

def get_mem_usage():
    mem_info = psutil.virtual_memory()
    total_memory = {mem_info.total / (1024**3)}
    used_memory = {mem_info.used / (1024**3)}
    useage_percent = {mem_info.percent}
    return total_memory, used_memory

def get_disk_info():
    disk = psutil.disk_usage('/')
    used_disk = {disk.total / (1024**3)}
    return disk, used_disk

if __name__ == '__main__':
    system_info()
    get_gpu_temps()
    get_cpu_temps()
    get_cpu_usage()
    get_mem_usage()
    get_disk_info()
