import requests
from bs4 import BeautifulSoup
import re
import json


def scrape_devicehunt():
    url = "https://devicehunt.com/all-usb-vendors"
    print(f"Fetching data from {url}...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    page_text = soup.get_text(" ")

    # 3. Extract data using Regex
    # Pattern looks for: "Vendor ID <HEX> Vendor Name <NAME> More Vendor Devices"
    # This pattern is consistent across the entire page list.
    pattern = r"Vendor ID\s+([0-9a-fA-F]+)\s+Vendor Name\s+(.*?)\s+More Vendor Devices"
    matches = re.findall(pattern, page_text)

    print(f"Found {len(matches)} vendors.")

    # 4. Format into the requested JSON structure
    output_data = {"vendors": {}}

    for vid, name in matches:
        # Standardize ID: ensure lowercase and add '0x' prefix
        clean_id = f"0x{vid.lower()}"
        clean_name = name.strip()

        # Handle cases where name might be placeholder "???"
        if clean_name == "???":
            clean_name = "Unknown Vendor"

        output_data["vendors"][clean_id] = clean_name

    filename = "usb_vendors.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Successfully saved to {filename}")


if __name__ == "__main__":
    scrape_devicehunt()