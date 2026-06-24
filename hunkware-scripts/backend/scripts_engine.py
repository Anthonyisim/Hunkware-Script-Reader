"""
Script generation engine.

Templates are transcribed directly from the company's own training PDFs
(Welcome_and_Confirmation_Call_Scripts.pdf, post_job_call_guide_revised.pdf)
so callers see the exact same wording they're trained on, just with the
job fields filled in.

Two service-type variants are supported for Welcome/Confirmation since the
source PDF has separate scripts for Move/Move Labor vs Junk Removal.
Midpoint Confirmation has no separate source script (the source PDF only
defines a *timing rule* for it: "add a midpoint check-in 2 weeks before
service" -- no separate wording was provided) so it reuses the
Confirmation Call structure with lighter, check-in framing. This should
be reviewed/edited by the team once final wording is supplied.
"""

SCRIPT_TYPES = {
    "welcome": "Welcome Call",
    "confirmation": "Confirmation Call",
    "midpoint": "Midpoint Confirmation Call",
    "happy": "Happy / Post-Job Call",
}


def _is_junk(service_type):
    return bool(service_type) and "junk" in service_type.lower()


def _fmt_items(items):
    if not items:
        return "[items not listed]"
    return ", ".join(items)


def _fmt(value, fallback="[not provided]"):
    if value is None or value == "":
        return fallback
    return value


def _service_label(service_type):
    if not service_type:
        return "[move / junk removal / labor]"
    s = service_type.lower()
    if "junk" in s:
        return "junk removal"
    if "labor" in s:
        return "move labor"
    return "moving"


def generate_welcome_call(job, caller_name="[Name]"):
    name = _fmt(job.get("client_name"))
    date = _fmt(job.get("service_date"))
    window = _fmt(job.get("arrival_window"))
    origin = _fmt(job.get("origin_address"))
    dest = _fmt(job.get("destination_address"))

    if _is_junk(job.get("service_type")):
        items = _fmt_items(job.get("items"))
        address = origin if origin != "[not provided]" else _fmt(job.get("destination_address"))
        return f"""WELCOME CALL — Junk Removal

Opening:
Good morning/afternoon, my name is {caller_name} calling from College HUNKS Hauling Junk and Moving. May I speak with {name}?

Local connection:
Hi {name}, thank you so much for booking your junk removal service with us. I am calling from our local Merrillville office near Route 30, and I wanted to make sure you have a local contact before your service date.

Confirm basics:
I see we have you scheduled for {date} with an arrival window of {window}. The service address we have is {address}.

Confirm items:
In the notes, we are scheduled to remove {items}. Is that still correct, or has anything been added or removed?

What happens next:
You will receive a confirmation call closer to your service date. On service day, the team captain will call when they are about 20 minutes away so you have an exact ETA.

Close:
Do you have any questions I can answer right now? We appreciate you choosing us and look forward to helping you."""

    return f"""WELCOME CALL — Move / Move Labor

Opening:
Good morning/afternoon, my name is {caller_name} calling from College HUNKS Hauling Junk and Moving. May I speak with {name}?

Local connection:
Hi {name}, thank you so much for booking your moving service with us. I am calling from our local Merrillville office near Route 30, and I wanted to make sure you have a local contact as we get closer to your service date.

Confirm basics:
I see we have you scheduled for {date} with an arrival window of {window}. We have you moving from {origin} to {dest}.

What happens next:
You will receive a confirmation call a few days before service so we can review any updates to your appointment, inventory, or timing. On move day, the team captain will call when they are about 20 minutes away.

Helpful add-ons:
If you have items you do not want anymore, we offer junk removal before or on the same day. We also sell packing boxes, and box delivery is complimentary when purchased from us.

Close:
Do you have any questions I can answer right now? Again, my name is {caller_name}, and we look forward to helping you on your service date."""


def generate_confirmation_call(job, caller_name="[Name]"):
    name = _fmt(job.get("client_name"))
    date = _fmt(job.get("service_date"))
    window = _fmt(job.get("arrival_window"))
    hunks = _fmt(job.get("num_hunks"), "[#]")
    hours = _fmt(job.get("estimated_hours"))
    amount = _fmt(job.get("amount"))
    service_label = _service_label(job.get("service_type"))

    if _is_junk(job.get("service_type")):
        items = _fmt_items(job.get("items"))
        return f"""CONFIRMATION CALL — Junk Removal

Opening:
Good morning/afternoon, this is {caller_name} from College HUNKS Hauling Junk and Moving. May I speak with {name}?

Purpose:
Hi {name}, I am giving you a quick call because we have you scheduled for junk removal on {date}, and I am completing your final confirmation call.

Confirm items:
In the notes, we are scheduled to remove {items}. Is that still correct, or has anything been added or removed?

Confirm location:
Where are the items located: inside, outside, garage, basement, upstairs, curbside, or storage unit?

Confirm arrival window:
Your team is scheduled to arrive within your arrival window of {window}. We strive to arrive at the beginning of the window. Either way, the team captain will call when they are about 20 minutes away.

Close:
Do you have any questions? We accept cash, check, and major debit or credit cards. We look forward to servicing you."""

    return f"""CONFIRMATION CALL — Move / Move Labor

Opening:
Good morning/afternoon, this is {caller_name} from College HUNKS Hauling Junk and Moving. May I speak with {name}? I am reaching out because your service day is coming up.

Readiness check:
Do you have everything ready for your move? We have everything set on our end.

Confirm schedule:
We have your team arriving on {date} with an arrival window of {window}. We strive to arrive at the beginning of the arrival window. Either way, the team captain will call when they are about 20 minutes away.

Confirm service:
We have you scheduled for {service_label} with {hunks} HUNKS. Your service is estimated to take about {hours} hours with an estimated cost of approximately ${amount}.

Confirm expectations:
As long as everything is boxed, packed, move-ready, and the inventory is consistent with what we have listed, we should be ready to rock and roll.

Close:
Do you have any questions about timing, payment, or what to expect? We accept cash, check, and major debit or credit cards."""


def generate_midpoint_call(job, caller_name="[Name]"):
    """
    No standalone script was provided for the midpoint check-in — the source
    PDF only specifies the timing rule (2 weeks before service, for jobs
    booked more than 2 weeks out). This reuses the Confirmation Call
    structure with check-in framing instead of final-confirmation framing.
    Swap in your own wording here once it's finalized.
    """
    name = _fmt(job.get("client_name"))
    date = _fmt(job.get("service_date"))
    window = _fmt(job.get("arrival_window"))
    hunks = _fmt(job.get("num_hunks"), "[#]")
    hours = _fmt(job.get("estimated_hours"))
    amount = _fmt(job.get("amount"))
    service_label = _service_label(job.get("service_type"))

    items_line = ""
    if _is_junk(job.get("service_type")):
        items_line = f"\nConfirm items:\nIn the notes, we are scheduled to remove {_fmt_items(job.get('items'))}. Is that still correct, or has anything been added or removed?\n"

    return f"""MIDPOINT CONFIRMATION CALL
(Note: standalone wording not yet provided — using Confirmation Call structure with check-in framing. Update once final script is supplied.)

Opening:
Good morning/afternoon, this is {caller_name} from College HUNKS Hauling Junk and Moving. May I speak with {name}? I'm calling for a quick midpoint check-in ahead of your upcoming service.

Readiness check:
Your service is still a couple of weeks out — we have you on {date} with an arrival window of {window}. Has anything changed on your end since we last spoke?
{items_line}
Confirm service:
We currently have you down for {service_label} with {hunks} HUNKS, estimated to take about {hours} hours, at an estimated cost of approximately ${amount}. Does that still sound right?

Close:
You'll get a final confirmation call closer to your service date. Is there anything I can help with in the meantime?"""


def generate_happy_call(job, va_name="[VA Name]"):
    name = _fmt(job.get("client_name"))
    service_label = _service_label(job.get("service_type"))

    return f"""HAPPY / POST-JOB CALL

Before the call — closeout check:
- Job status: confirm marked Completed, not Scheduled.
- Balance: confirm balance due is $0.00.
- Billing: verify service total matches payment amounts on the billing screen.
- If anything is off: notify management before completing follow-up.

Opening:
Hi {name}, this is {va_name} calling from College HUNKS in Merrillville. I just wanted to thank you again for trusting us with your {service_label} service. We really appreciate your business.

Service check-in:
How did everything go with your service?

Rapport question (pick one matching the service):
- Moving: "Are you getting settled into your new place yet?" or "Have you had a chance to start unpacking?"
- Junk: "How does it feel to have that space cleared out?"
- Labor: "Were you able to get everything where you wanted it?"

Cross-sell:
- If junk client: "We also offer moving and labor service if you ever need help in the future."
- If moving or labor client: "We also offer junk removal if you decide there are items you do not want to keep."

Repeat customer offer:
Repeat customers receive $30 off any service booked within the next 60 days.

IF SERVICE WENT WELL — Google review ask:
"I am going to send the Google review link to your text right now. If you happened to already receive a link, that was likely our internal feedback link, which helps us monitor service on the staff side. But the Google review is the best place to share your experience because it publicly highlights your team and their hard work. Would you be able to take just one minute to complete it as soon as we hang up? A 5-star review and even a short sentence or two about your experience really helps, because the team earns bonuses and recognition for exceptional service. I will keep an eye out for it, and if you have any issues with the link, I would be happy to follow up and help."

Review link (text or email):
"Thank you again for trusting College HUNKS with your move/junk removal service. We'd be grateful if you took a moment to leave us a Google review. Your feedback helps our local team so much: https://g.page/r/CYrUB6soK5ilEBM/review"

IF SERVICE DID NOT GO WELL — do not ask for a review:
"Thank you for letting me know. I am going to forward your concerns to management, and you will receive a callback with next steps."
Document the concern clearly and notify management."""


GENERATORS = {
    "welcome": generate_welcome_call,
    "confirmation": generate_confirmation_call,
    "midpoint": generate_midpoint_call,
    "happy": generate_happy_call,
}


def generate_script(script_type, job, caller_name="[Name]"):
    if script_type not in GENERATORS:
        raise ValueError(f"Unknown script type: {script_type}")
    if script_type == "happy":
        return GENERATORS[script_type](job, va_name=caller_name)
    return GENERATORS[script_type](job, caller_name=caller_name)
