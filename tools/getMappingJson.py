import re
from urllib.request import urlopen

#WARNING: Running this script will overwrite the existing usb_database.json file

raw = urlopen("http://www.linux-usb.org/usb.ids").read().decode("utf-8", "ignore")

vendors = {}
devices = {}
classes = {}
subclasses = {}
protocols = {}

current_vid = None
current_class = None

for line in raw.splitlines():
    line = line.rstrip()
    if not line or line.startswith("#"):
        continue

    # Vendor
    if re.match(r"^[0-9a-fA-F]{4}\s", line):
        vid = "0x" + line[:4].lower()
        vendors[vid] = line[6:].strip()
        current_vid = vid
        continue

    # Device
    if line.startswith("\t") and re.match(r"\t[0-9a-fA-F]{4}\s", line):
        pid = "0x" + line[1:5].lower()
        name = line[7:].strip()
        if name:
            devices[f"{current_vid}:{pid}"] = name
        continue

    # Class
    if line.startswith("C "):
        cls = "0x" + line[2:4].lower()
        name = line[6:].strip()
        if name:
            classes[cls] = name
        current_class = cls[2:]
        continue

    # Subclass
    if line.startswith("\t") and current_class and re.match(r"\t[0-9a-fA-F]{2}\s", line):
        sub = line[1:3].lower()
        name = line[5:].strip()
        if name:
            subclasses[f"{current_class}:{sub}"] = name
        continue

    # Protocol
    if line.startswith("\t\t") and current_class and re.match(r"\t\t[0-9a-fA-F]{2}\s", line):
        proto = line[2:4].lower()
        name = line[6:].strip()
        last_sub = list(subclasses.keys())[-1].split(":")[1] if subclasses else "00"
        if name:
            protocols[f"{current_class}:{last_sub}:{proto}"] = name

result = {
    "vendors": vendors,
    "devices": devices,
    "classes": classes,
    "subclasses": subclasses,
    "protocols": protocols
}

import json
with open("usb_database.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Success! {len(vendors)} vendors · {len(devices)} devices · {len(classes)} classes")