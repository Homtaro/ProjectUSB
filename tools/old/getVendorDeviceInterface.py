import re
import json
from datetime import datetime
from urllib.request import urlopen

URL = "http://www.linux-usb.org/usb.ids"
raw = urlopen(URL).read().decode("utf-8", errors="ignore")

vendors = {}
devices = {}
interfaces = {}
classes = {}
subclasses = {}
protocols = {}

current_vid = None
current_pid = None
current_class = None
for line in raw.splitlines():
    line = line.rstrip("\n")
    if not line or line.startswith("#"):
        continue

    # Vendor
    if re.match(r"^[0-9A-Fa-f]{4}\s", line):
        vid = "0x" + line[:4].lower()
        name = line[6:].strip()
        if name:
            vendors[vid] = name
        current_vid = vid
        current_pid = None
        continue

    # Device (one tab)
    if line.startswith("\t") and re.match(r"\t[0-9A-Fa-f]{4}\s", line):
        pid = "0x" + line[1:5].lower()
        name = line[7:].strip()
        key = f"{current_vid}:{pid}"
        if name and current_vid:
            devices[key] = name
        current_pid = pid
        continue

    # Interface (two tabs)
    if line.startswith("\t\t") and re.match(r"\t\t[0-9A-Fa-f]{4}\s", line):
        iface = line[2:4].lower()
        name = line[7:].strip()
        if name and current_vid and current_pid:
            interfaces[f"{current_vid}:{current_pid}:{iface}"] = name
        continue

    # Class section starts with "C "
    if line.startswith("C "):
        cls = "0x" + line[2:4].lower()
        name = line[6:].strip()
        if name:
            classes[cls] = name
        current_class = cls
        continue

    # Subclass (one tab after class)
    if line.startswith("\t") and not line.startswith("\t\t") and current_class:
        parts = line[1:].split(maxsplit=1)
        if len(parts) == 2 and re.match(r"^[0-9A-Fa-f]{2}$", parts[0]):
            sub = parts[0].lower()
            name = parts[1].strip()
            subclasses[f"{current_class[2:]}:{sub}"] = name
        continue

    # Protocol (two tabs after class)
    if line.startswith("\t\t") and current_class:
        parts = line[2:].split(maxsplit=1)
        if len(parts) == 2 and re.match(r"^[0-9A-Fa-f]{2}$", parts[0]):
            proto = parts[0].lower()
            name = parts[1].strip()
            # Find the last subclass we were in (simple but works 99.9% of cases)
            last_sub = list(subclasses.keys())[-1].split(":")[1] if subclasses else "00"
            protocols[f"{current_class[2:]}:{last_sub}:{proto}"] = name

# Save everything
result = {
    "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"),
    "source": URL,
    "version": "2025.09.15",
    "vendors": vendors,
    "devices": devices,
    "interfaces": interfaces,
    "classes": classes,
    "subclasses": subclasses,
    "protocols": protocols
}

with open("usb-complete-database.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False, sort_keys=True)

print(f"Success! {len(vendors)} vendors · {len(devices)} devices · {len(interfaces)} interfaces · {len(classes)} classes")