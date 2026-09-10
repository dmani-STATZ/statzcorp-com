import re


# Expected to grow as new disposable and anonymous-publishing domains appear.
BLOCKLISTED_DOMAINS = frozenset(
    {
        'telegra.ph',
        't.me',
        'bit.ly',
        'tinyurl.com',
        'is.gd',
        'cutt.ly',
        'rebrand.ly',
        'shorturl.at',
    }
)

URL_RE = re.compile(r'https?://|www\.', re.IGNORECASE)
SCHEME_RE = re.compile(r'https?://', re.IGNORECASE)
BARE_WWW_RE = re.compile(r'(?<![\w.])www\.', re.IGNORECASE)


def score_submission(
    name: str,
    company: str,
    email: str,
    phone: str,
    message: str,
) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    url_count = len(URL_RE.findall(message))
    if url_count:
        score += 3
        reasons.append('url_in_message')
    if url_count >= 2:
        score += 2
        reasons.append('multiple_urls')

    message_lower = message.lower()
    if any(
        re.search(rf'(?<![\w.-]){re.escape(domain)}(?![\w.-])', message_lower)
        for domain in BLOCKLISTED_DOMAINS
    ):
        score += 4
        reasons.append('blocklisted_domain')

    alphabetic = [character for character in message if character.isalpha()]
    if (
        len(message) >= 20
        and alphabetic
        and sum(character.isupper() for character in alphabetic) / len(alphabetic) > 0.30
    ):
        score += 2
        reasons.append('excessive_caps')

    if not any(character.isspace() for character in name) and len(name) > 12:
        score += 2
        reasons.append('concatenated_name')

    name_lower = name.lower()
    email_local = email.partition('@')[0].lower()
    if not any(
        name_lower[index:index + 4] in email_local
        for index in range(max(0, len(name_lower) - 3))
    ):
        score += 1
        reasons.append('name_email_mismatch')

    phone_digits = ''.join(character for character in phone if character.isdigit())
    if len(phone_digits) not in (10, 11):
        score += 1
        reasons.append('implausible_phone')

    return score, reasons


def defang_urls(text: str) -> str:
    def replace_scheme(match):
        return 'hxxps://' if match.group(0).lower().startswith('https') else 'hxxp://'

    def replace_www(match):
        return f'{match.group(0)[:3]}[.]'

    return BARE_WWW_RE.sub(replace_www, SCHEME_RE.sub(replace_scheme, text))
