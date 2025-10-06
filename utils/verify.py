# utils/verify.py
import time, hmac, hashlib
from config import SLACK_SIGNING_SECRET

def verify_slack(req) -> bool:
    ts = req.headers.get("X-Slack-Request-Timestamp", "")
    sig = req.headers.get("X-Slack-Signature", "")
    if not ts or not sig:
        return False
    if abs(time.time() - int(ts)) > 60 * 5:
        return False
    body = req.get_data().decode("utf-8")
    base = f"v0:{ts}:{body}".encode("utf-8")
    my_sig = "v0=" + hmac.new(SLACK_SIGNING_SECRET.encode("utf-8"), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(my_sig, sig)
