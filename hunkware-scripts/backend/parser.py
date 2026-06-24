"""
Work order PDF parser for College HUNKS work orders.

Extracts the fields needed to populate call scripts:
client_name, service_date, service_type, arrival_window,
origin_address, destination_address, num_hunks, estimated_hours,
amount, items, job_id, phone, email

Built against the real labeled text layout produced by the
work order PDF export. Falls back gracefully (returns None / empty)
for any field it cannot confidently find, so the UI can prompt a human
to fill the gap rather than guessing.
"""

import re
import pdfplumber


def _search(pattern, text, group=1, flags=re.IGNORECASE):
    m = re.search(pattern, text, flags)
    if not m:
        return None
    return m.group(group).strip()


def extract_text(file_stream_or_path):
    """Extract raw text from every page of the PDF, joined together."""
    pages_text = []
    with pdfplumber.open(file_stream_or_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            pages_text.append(t)
    return "\n".join(pages_text)


def parse_work_order(file_stream_or_path):
    """
    Parse a College HUNKS work order PDF and return a dict of fields.
    Any field not found is set to None (or [] for items) so the caller
    can flag it for manual entry / review.
    """
    text = extract_text(file_stream_or_path)

    data = {
        "job_id": _search(r"Job ID:\s*([A-Za-z0-9\-]+)", text),
        "client_name": _search(r"Name:\s*([A-Za-z .,'\-]+?)(?:\n|Company Name)", text),
        "phone": _search(r"Phone:\s*([\d()\-\s]+?)(?:\n|Cell)", text),
        "email": _search(r"E-?Mail:\s*([^\s\n]+@[^\s\n]+)", text),
        "service_date": _search(r"Job Date:\s*([A-Za-z]+ \d{1,2},\s*\d{4})", text),
        "arrival_window": _search(r"Job Time:\s*([\d:]+\s*[APMapm]{2}\s*-\s*[\d:]+\s*[APMapm]{2})", text),
        "service_type": _search(r"^WORK ORDER\s*\n?\s*([A-Za-z &/]+)", text, flags=re.MULTILINE),
        "status": _search(r"Status:\s*([A-Za-z]+)", text),
        "origin_address": _search(r"Origin Address:\s*([^\|]+?)\s*\|", text),
        "destination_address": _search(r"Destination Address:\s*([^\|]+?)\s*\|", text),
        "num_hunks": _search(r"using\s*(\d+)\s*HUNKS", text),
        "estimated_hours": _search(r"estimated the move to last\s*([\d.]+)\s*hours", text),
        "amount": _search(r"estimated total cost of this move is\s*\$([\d,]+\.\d{2})", text),
        "hourly_rate": _search(r"hourly rate.*?is\s*\$([\d.]+)\s*per hour", text),
        "ref_number": _search(r"REF\s*#([A-Z0-9\-]+)", text),
    }

    # Fallback for origin/destination if the "Move Factors" quote block isn't present
    # (e.g. junk removal jobs use a single "Service address" instead of origin/destination)
    if not data["origin_address"]:
        data["origin_address"] = _search(
            r"Pick-Up Location\s*\n*\s*([^\n]+,\s*[A-Z]{2},?\s*\d{5})", text
        )
    if not data["destination_address"]:
        data["destination_address"] = _search(
            r"Destination Location\s*\n*\s*([^\n]+,\s*[A-Z]{2},?\s*\d{5})", text
        )

    # Item / inventory list
    items = []
    inv_match = re.search(r"INVENTORY:(.*?)(?:PACKING SERVICES:|##### End Quote|\Z)", text, re.DOTALL)
    if inv_match:
        block = inv_match.group(1)
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("---") or "Room:" in line:
                continue
            if line.startswith("-"):
                items.append(line.lstrip("- ").strip())
    data["items"] = items

    # Clean service_type (work order header sometimes picks up extra words)
    if data["service_type"]:
        data["service_type"] = data["service_type"].strip()

    return data
