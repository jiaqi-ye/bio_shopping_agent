import json
from datetime import datetime

import requests

API_URL = "http://127.0.0.1:8000"


def prompt_int(label: str, default: int) -> int:
    value = input(f"{label} [{default}]: ").strip()
    return int(value) if value else default


def prompt_str(label: str, default: str) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def main() -> None:
    print("Research Animals Procurement Agent CLI")
    strain = prompt_str("Strain", "C57BL/6J")
    quantity = prompt_int("Quantity", 60)
    date_str = prompt_str("Experiment start date (YYYY-MM-DD)", datetime.today().strftime("%Y-%m-%d"))
    approved_quota = prompt_int("Approved IACUC quota", 50)

    payload = {
        "strain": strain,
        "quantity": quantity,
        "experiment_start_date": date_str,
        "approved_quota": approved_quota,
    }

    resp = requests.post(f"{API_URL}/procure", json=payload, timeout=10)
    if resp.status_code != 200:
        print("Procurement failed:", resp.text)
        alt = resp.headers.get("X-Alt-Strains")
        if alt:
            print("Recommended equivalent strains:", alt)
        return

    data = resp.json()
    print("Selected vendors:", ", ".join(data["selected_vendors"]))
    print("Latest order date:", data["latest_order_date"])
    print("Compliance:", data["compliance"])
    print("Cage check:", data["cages"])
    print("Allocation:")
    for a in data["allocation"]:
        print(f"  - {a['vendor_name']}: {a['quantity']} mice @ ${a['unit_price']}/ea (ship ${a['shipping_cost']})")
    print("RFQ JSON:")
    print(json.dumps(data["rfq"], indent=2))


if __name__ == "__main__":
    main()
