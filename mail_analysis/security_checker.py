import re

class EmailSecurityChecker:
    # takes the return value from GmailConnector's get_message_details function and performs all checks
    def __init__(self, message_details: dict):
        self.details = message_details
        self.headers = message_details.get('headers', [])
        self.sender = message_details.get('from', '')
        self.auth_results = message_details.get('auth_results', '').lower()

    # simplifies SPF, DKIM, and DMARC results
    def extract_auth_summary(self):
        summary = []
        for protocol in ['spf', 'dkim', 'dmarc']:
            if f"{protocol}=pass" in self.auth_results:
                summary.append(f"{protocol}:pass")
            elif f"{protocol}=fail" in self.auth_results:
                summary.append(f"{protocol}:fail")
            else:
                summary.append(f"{protocol}:unknown")
        return " ".join(summary)

    # checks if the 'from' and 'reply-to' fields match
    def check_reply_to_match(self):
        sender = ''
        reply_to = ''

        for header in self.headers:
            if header['name'].lower() == 'from':
                sender = header['value']
            elif header['name'].lower() == 'reply-to':
                reply_to = header['value']
        # returns True or False
        return reply_to.strip().lower() == sender.strip().lower()

    # checks if the sender's domain appears in the auth-results
    def check_domain_match(self):
        try:
            domain_full = self.sender.split('@')[-1].lower().strip('>') # clean the ">" sign and get the domain part
            match = re.search(r"([^.@]+)\.(com|net|org|edu|gov|mil|co\.uk|io|ai)$", domain_full)
            domain = match.group(1) + "." + match.group(2) if match else domain_full
            return domain in self.auth_results
        except:
            return False
        

