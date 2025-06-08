# hardware_info_agent.py
"""
Hardware Information Agent for Nina
Gets system hardware information including GPU, CPU, RAM, etc.
"""

import subprocess
import platform
import psutil
import json
import os
from datetime import datetime

class HardwareInfoAgent:
    """Agent to get hardware information"""
    
    def __init__(self):
        self.type = "hardware_agent"
        self.role = "hardware"
        self.agent_name = "HAL"
        
    def get_gpu_info(self):
        """Get GPU information"""
        try:
            # Try nvidia-smi first for NVIDIA GPUs
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', 
                                       '--format=csv,noheader'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return f"NVIDIA GPU: {result.stdout.strip()}"
            except:
                pass
                
            # Use WMI for Windows
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 
                                       'get', 'name,adapterram,driverversion'],
                                      capture_output=True, text=True, shell=True)
                lines = result.stdout.strip().split('\n')
                gpus = []
                for line in lines[1:]:  # Skip header
                    parts = line.strip().split()
                    if parts and parts[0] != '':
                        gpu_name = ' '.join(parts[:-2]) if len(parts) > 2 else ' '.join(parts)
                        gpus.append(gpu_name)
                return "GPUs: " + ', '.join(gpus) if gpus else "No GPU information found"
                
        except Exception as e:
            return f"Error getting GPU info: {str(e)}"
            
    def get_cpu_info(self):
        """Get CPU information"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'cpu', 'get', 'name,numberofcores,maxclockspeed'],
                                      capture_output=True, text=True, shell=True)
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Parse the output
                    headers = lines[0].split()
                    values = ' '.join(lines[1:]).strip()
                    return f"CPU: {values}"
            
            # Fallback using psutil
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            return f"CPU: {cpu_count} cores, {cpu_freq.max:.2f} MHz max frequency"
            
        except Exception as e:
            return f"Error getting CPU info: {str(e)}"
            
    def get_ram_info(self):
        """Get RAM information"""
        try:
            # Use psutil for cross-platform compatibility
            ram = psutil.virtual_memory()
            total_gb = ram.total / (1024**3)
            used_gb = ram.used / (1024**3)
            available_gb = ram.available / (1024**3)
            
            info = f"RAM: {total_gb:.1f} GB total, {used_gb:.1f} GB used, {available_gb:.1f} GB available"
            
            # Try to get RAM speed on Windows
            if platform.system() == "Windows":
                try:
                    result = subprocess.run(['wmic', 'memorychip', 'get', 'speed'],
                                          capture_output=True, text=True, shell=True)
                    lines = result.stdout.strip().split('\n')
                    speeds = [line.strip() for line in lines[1:] if line.strip() and line.strip() != '']
                    if speeds and speeds[0]:
                        info += f", {speeds[0]} MHz"
                except:
                    pass
                    
            return info
            
        except Exception as e:
            return f"Error getting RAM info: {str(e)}"
            
    def get_disk_info(self):
        """Get disk information"""
        try:
            disks = []
            for partition in psutil.disk_partitions():
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
                    
                usage = psutil.disk_usage(partition.mountpoint)
                total_gb = usage.total / (1024**3)
                used_gb = usage.used / (1024**3)
                free_gb = usage.free / (1024**3)
                
                disk_info = f"{partition.device} ({partition.fstype}): "
                disk_info += f"{total_gb:.1f} GB total, {used_gb:.1f} GB used, {free_gb:.1f} GB free"
                disks.append(disk_info)
                
            return "Disks:\n" + '\n'.join(disks)
            
        except Exception as e:
            return f"Error getting disk info: {str(e)}"
            
    def get_all_hardware_info(self):
        """Get all hardware information"""
        info = []
        info.append("=== SYSTEM HARDWARE INFORMATION ===")
        info.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        info.append(f"Computer: {platform.node()}")
        info.append(f"System: {platform.system()} {platform.release()}")
        info.append(f"Architecture: {platform.machine()}")
        info.append("")
        
        info.append("=== CPU ===")
        info.append(self.get_cpu_info())
        info.append("")
        
        info.append("=== GPU ===")
        info.append(self.get_gpu_info())
        info.append("")
        
        info.append("=== MEMORY ===")
        info.append(self.get_ram_info())
        info.append("")
        
        info.append("=== STORAGE ===")
        info.append(self.get_disk_info())
        info.append("")
        
        # Additional system info
        try:
            info.append("=== MOTHERBOARD ===")
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'baseboard', 'get', 'manufacturer,product'],
                                      capture_output=True, text=True, shell=True)
                info.append(result.stdout.strip())
        except:
            pass
            
        return '\n'.join(info)
        
    def save_hardware_info(self, filepath=None):
        """Save hardware info to file"""
        if filepath is None:
            filepath = os.path.join(os.path.expanduser("~"), "Desktop", "hardware_info.txt")
            
        hardware_info = self.get_all_hardware_info()
        
        try:
            with open(filepath, 'w') as f:
                f.write(hardware_info)
            return True, filepath, hardware_