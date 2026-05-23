import ipaddress

def ip_to_int(ip_str):
    try:
        return int(ipaddress.IPv4Address(ip_str.strip()))
    except Exception:
        return None


def int_to_ip(ip_int):
    return str(ipaddress.IPv4Address(ip_int))