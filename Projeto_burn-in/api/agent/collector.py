"""
collector.py
Coleta as informações de hardware da máquina:
MAC Ethernet, número de série, CPU, RAM, SSD e GPU (quando disponível).
"""

import uuid
import subprocess
import platform
import psutil


def get_mac_address() -> str:
    """Retorna o MAC do primeiro adaptador Ethernet físico encontrado."""
    for name, addrs in psutil.net_if_addrs().items():
        # Ignora loopback e interfaces virtuais comuns
        if any(skip in name.lower() for skip in ["lo", "docker", "veth", "virbr", "vmnet"]):
            continue
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                mac = addr.address
                if mac and mac != "00:00:00:00:00:00":
                    return mac
    # Fallback: MAC gerado a partir do hostname (determinístico)
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, platform.node()))


def get_serial_number() -> str | None:
    """Tenta obter o número de série via dmidecode (requer root no Linux)."""
    try:
        result = subprocess.run(
            ["dmidecode", "-s", "system-serial-number"],
            capture_output=True, text=True, timeout=5
        )
        serial = result.stdout.strip()
        if serial and serial.lower() not in ("", "not specified", "to be filled by o.e.m."):
            return serial
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def get_cpu_info() -> dict:
    freq = psutil.cpu_freq()
    return {
        "modelo": platform.processor() or "Desconhecido",
        "nucleos_fisicos": psutil.cpu_count(logical=False),
        "nucleos_logicos": psutil.cpu_count(logical=True),
        "frequencia_mhz": round(freq.max, 0) if freq else None,
    }


def get_ram_info() -> dict:
    ram = psutil.virtual_memory()
    return {
        "total_gb": round(ram.total / (1024 ** 3), 2),
    }


def get_disk_info() -> list[dict]:
    disks = []
    for part in psutil.disk_partitions(all=False):
        if "loop" in part.device:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "dispositivo": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 2),
            })
        except PermissionError:
            continue
    return disks


def get_gpu_info() -> list[dict] | None:
    """Tenta detectar GPUs via nvidia-smi. Retorna None se não houver."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            gpus = []
            for line in result.stdout.strip().splitlines():
                parts = line.split(",")
                if len(parts) == 2:
                    gpus.append({
                        "modelo": parts[0].strip(),
                        "memoria": parts[1].strip(),
                    })
            return gpus if gpus else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def collect() -> dict:
    """Retorna um dicionário completo com todas as informações do equipamento."""
    return {
        "mac_address": get_mac_address(),
        "serial": get_serial_number(),
        "hostname": platform.node(),
        "sistema_operacional": f"{platform.system()} {platform.release()}",
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "discos": get_disk_info(),
        "gpus": get_gpu_info(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(collect(), indent=2, ensure_ascii=False))