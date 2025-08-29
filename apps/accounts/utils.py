DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "temp-mail.org",
    "guerrillamail.com",
    "yopmail.com",
    "getnada.com",
    "trashmail.com",
    "tempmail.dev",
}

def is_disposable_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1].lower().strip()
    return domain in DISPOSABLE_DOMAINS
