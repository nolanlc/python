"""
Extract Voter ID, Full Name, Address, and Address Type for the first 3 voter records
from VRC260204 Full Orig.xlsx. Address type is resolved via Google Address Validation API.
"""

import urllib.request
import urllib.error
import json
import openpyxl

FILE = "VRC260204 Full Orig.xlsx"
GOOGLE_API_KEY = "AIzaSyChQqNSaT0B364-tMWsHzYsAHZ5-5m31nA"
VALIDATE_URL = f"https://addressvalidation.googleapis.com/v1:validateAddress?key={GOOGLE_API_KEY}"


def get_address_type(address: str) -> str:
    """Call Google Address Validation API and return the address type from metadata."""
    payload = json.dumps({"address": {"addressLines": [address]}}).encode()
    req = urllib.request.Request(
        VALIDATE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return f"API error {e.code}"

    metadata = data.get("result", {}).get("metadata", {})
    if metadata.get("residential"):
        return "Residential"
    if metadata.get("business"):
        return "Business"
    if metadata.get("poBox"):
        return "PO Box"
    return "Unknown"

def build_full_name(title, first, middle, last, suffix):
    """Assemble full name from component parts."""
    parts = [title, first, middle, last, suffix]
    return " ".join(p.strip() for p in parts if p)

def build_address(house_num, street, city, state, zip_code):
    """Assemble residence address."""
    # ResidenceAddress (col 10) already contains the full street address
    addr_parts = [street, city, state, str(zip_code) if zip_code else ""]
    return ", ".join(p for p in addr_parts if p)

def get_record_limit():
    """Prompt the user for how many records to extract. Returns None for all records."""
    while True:
        answer = input("How many Voter ID records do you want to extract? (enter a number or ALL): ").strip()
        if answer.upper() == "ALL":
            return None
        if answer.isdigit() and int(answer) > 0:
            return int(answer)
        print("  Please enter a positive number or ALL.")

def get_output_filter():
    """Prompt the user for which records to display."""
    print("Output options:")
    print("  1 - All Address Type records")
    print("  2 - Non-Residential records only")
    while True:
        answer = input("Enter 1 or 2: ").strip()
        if answer in ("1", "2"):
            return answer
        print("  Please enter 1 or 2.")

def main():
    limit = get_record_limit()
    output_filter = get_output_filter()
    max_row = None if limit is None else limit + 1  # +1 to account for header row

    wb = openpyxl.load_workbook(FILE, read_only=True)
    ws = wb.active

    # Read header row to map column names to indices
    headers = [cell for cell in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
    col = {name: idx for idx, name in enumerate(headers)}

    records = []
    api_call_count = 0
    for row in ws.iter_rows(min_row=2, max_row=max_row, values_only=True):
        voter_id   = row[col["VoterID"]]
        full_name  = build_full_name(
            row[col["VoterTitle"]],
            row[col["FirstName"]],
            row[col["MiddleName"]],
            row[col["LastName"]],
            row[col["NameSuffix"]],
        )
        address    = build_address(
            row[col["HouseNumber"]],
            row[col["ResidenceAddress"]],
            row[col["ResidenceCity"]],
            row[col["ResidenceState"]],
            row[col["ResidenceZipCode"]],
        )
        api_call_count += 1
        print(f"  API Call #{api_call_count}: Validating: {address}")
        addr_type  = get_address_type(address)
        party_name = row[col["PartyName"]] or ""
        records.append((voter_id, full_name, address, addr_type, party_name))

    wb.close()

    # Print tabular output
    hdr_id    = "Voter ID"
    hdr_name  = "Full Name"
    hdr_addr  = "Address"
    hdr_type  = "Address Type"
    hdr_party = "Party Name"

    w_id    = max(len(hdr_id),    max(len(str(r[0])) for r in records))
    w_name  = max(len(hdr_name),  max(len(r[1])       for r in records))
    w_addr  = max(len(hdr_addr),  max(len(r[2])       for r in records))
    w_type  = max(len(hdr_type),  max(len(r[3])       for r in records))
    w_party = max(len(hdr_party), max(len(r[4])       for r in records))

    sep = f"+{'-'*(w_id+2)}+{'-'*(w_name+2)}+{'-'*(w_addr+2)}+{'-'*(w_type+2)}+{'-'*(w_party+2)}+"
    fmt = f"| {{:<{w_id}}} | {{:<{w_name}}} | {{:<{w_addr}}} | {{:<{w_type}}} | {{:<{w_party}}} |"

    print(sep)
    print(fmt.format(hdr_id, hdr_name, hdr_addr, hdr_type, hdr_party))
    print(sep)

    # Tally counts per address type, starting each at 0
    counts = {"Residential": 0, "Business": 0, "PO Box": 0, "Unknown": 0}
    for voter_id, full_name, address, addr_type, party_name in records:
        counts[addr_type] = counts.get(addr_type, 0) + 1
        # Apply output filter: option 2 skips Residential records
        if output_filter == "2" and addr_type == "Residential":
            continue
        print(fmt.format(str(voter_id), full_name, address, addr_type, party_name))
    print(sep)

    # Print address type counts
    print("\nAddress Type Counts:")
    print(f"  {'Address Type':<15} {'Total Count'}")
    print(f"  {'-'*15} {'-'*11}")
    for addr_type, total in counts.items():
        print(f"  {addr_type:<15} {total}")

    # Write results to output.xlsx
    out_wb = openpyxl.Workbook()

    # Sheet 1: voter records (respecting the output filter)
    ws_out = out_wb.active
    ws_out.title = "Voter Records"
    ws_out.append(["Voter ID", "Full Name", "Address", "Address Type", "Party Name"])
    for voter_id, full_name, address, addr_type, party_name in records:
        if output_filter == "2" and addr_type == "Residential":
            continue
        ws_out.append([voter_id, full_name, address, addr_type, party_name])

    # Sheet 2: address type counts
    ws_counts = out_wb.create_sheet("Address Type Counts")
    ws_counts.append(["Address Type", "Total Count"])
    for addr_type, total in counts.items():
        ws_counts.append([addr_type, total])

    record_count = len(records) if limit is None else limit
    output_filename = f"voter_output_{record_count}.xlsx"
    out_wb.save(output_filename)
    print(f"\nResults saved to {output_filename}")

if __name__ == "__main__":
    main()
