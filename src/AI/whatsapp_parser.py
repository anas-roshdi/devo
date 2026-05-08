"""
WhatsApp Message Parser
========================
Cleans and splits raw WhatsApp chat export text into structured message blocks.
Handles Arabic numerals, emojis, noise words, and customer name detection.
"""

import re
from dataclasses import dataclass, field


# Arabic/Eastern numeral → Western digit mapping
ARABIC_NUMERALS = {
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
}

# Words to strip from product lines (not useful for matching)
NOISE_WORDS = ['تجهيز', 'ابا اطلب', 'ابي اطلب', 'اطلب', 'ابا', 'ابي']

# Product-related keywords (lines containing these are NOT customer names)
PRODUCT_KEYWORDS = [
    'كيلو', 'حبة', 'حبات', 'كيس', 'علبة', 'اعواد', 'عود',
    'مموج', 'بالدقة', 'لفائف', 'صوص', 'صوض', 'دقة', 'مشكل', 'مكس',
    'حامض', 'حار', 'حلو', 'سادة', 'ثيم', 'قمر',
]


@dataclass
class MessageBlock:
    """Represents one parsed WhatsApp message (= one potential invoice)."""
    date: str                     # YYYY-MM-DD
    raw_text: str                 # Original full message text
    content_lines: list           # Cleaned product lines
    customer_hint: str = None     # Detected customer name (or None)


class WhatsAppParser:
    """Parses raw WhatsApp chat export into MessageBlock objects."""

    def __init__(self, year=2026):
        self.year = year

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def parse(self, raw_text):
        """
        Parse a full WhatsApp chat export into message blocks.
        Each message becomes one potential invoice.
        
        Args:
            raw_text: The full pasted WhatsApp text.
        Returns:
            List of MessageBlock objects.
        """
        # Remove WhatsApp's invisible directional formatting characters (LRM, RLM, LRI, RLI, etc.)
        clean_text = re.sub(r'[\u200E\u200F\u202A-\u202E\u202A-\u202C\u2066-\u2069]', '', raw_text)
        
        text = self.arabic_to_western(clean_text)

        # WhatsApp header pattern (after numeral conversion):
        # [19/4, 6:12 ص] +966 56 316 5394: content
        # Also handle: [19/4, 6:12 م]
        pattern = r'\[(\d{1,2}/\d{1,2})[،,]\s*\d{1,2}:\d{2}\s*[صم]\](?:\s*[^:]+:\s*)?'
        headers = list(re.finditer(pattern, text))

        if not headers:
            # No WhatsApp headers found - treat entire text as one block
            block = self._build_block("", text)
            return [block] if block.content_lines else []

        blocks = []
        for i, header in enumerate(headers):
            date_match = header.group(1)  # e.g. "19/4"
            content_start = header.end()
            content_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            content = text[content_start:content_end].strip()

            # Convert date
            day, month = date_match.split('/')
            formatted_date = f"{self.year}-{int(month):02d}-{int(day):02d}"

            block = self._build_block(formatted_date, content)
            if block.content_lines:
                blocks.append(block)

        return blocks

    # ==========================================================
    # INTERNAL HELPERS
    # ==========================================================

    @staticmethod
    def arabic_to_western(text):
        """Convert Arabic/Eastern numerals (٠-٩) to Western digits (0-9)."""
        for ar, en in ARABIC_NUMERALS.items():
            text = text.replace(ar, en)
        return text

    def _build_block(self, date, content):
        """Parse a single message's content into a MessageBlock."""
        lines = [l.strip() for l in content.split('\n') if l.strip()]

        product_lines = []
        customer_hint = None

        for i, line in enumerate(lines):
            clean = self._clean_line(line)
            if not clean:
                continue

            # Determine if this line is a customer name or product line
            if self._is_customer_name(clean, i, len(lines)):
                # Strip delivery keywords for a cleaner customer name
                clean_name = re.sub(r'^(استلام|تسليم)\s*', '', clean)
                customer_hint = clean_name
            else:
                # Split line by ' و ', '+', or commas to handle multiple products on one line
                # Ignore splitting 'و' if it is followed by 'نص' or 'نصف'
                parts = re.split(r'\s+و\s*(?!(?:نص|نصف)\b)|\s*\+\s*|،|,', clean)
                for part in parts:
                    part = part.strip()
                    if part:
                        product_lines.append(part)

        # Fallback: check for inline customer reference (e.g. "لحمضها")
        if not customer_hint:
            customer_hint = self._find_inline_customer(content)

        return MessageBlock(
            date=date,
            raw_text=content,
            content_lines=product_lines,
            customer_hint=customer_hint
        )

    def _clean_line(self, line):
        """Remove emojis, noise words, and delivery instructions."""
        # Remove emojis (non-word, non-space, non-punctuation Unicode)
        line = re.sub(
            r'[\U0001F300-\U0001FAFF\U00002702-\U000027B0\U0000FE00-\U0000FE0F'
            r'\U0000200D\U00002600-\U000026FF\U00002B50]', '', line
        )

        # Remove noise words
        for noise in NOISE_WORDS:
            line = re.sub(r'\b' + re.escape(noise) + r'\b', '', line)

        return line.strip()

    def _is_customer_name(self, line, index, total):
        """
        Heuristic: a line is a customer name if it starts with 'استلام'/'تسليم',
        or if it's at the start/end, is short, and has no product keywords.
        """
        if not line:
            return False
            
        # Strong signal: starts with delivery keyword
        if line.startswith('استلام') or line.startswith('تسليم'):
            return True

        # Must be first or last line
        if index != 0 and index != total - 1:
            return False

        # Must NOT contain digits (unless it's a known format like '7شوال' which is handled above if it has 'استلام')
        if re.search(r'\d', line):
            return False

        # Must be short (≤ 4 words)
        if len(line.split()) > 4:
            return False

        # Must NOT contain product keywords
        if any(kw in line for kw in PRODUCT_KEYWORDS):
            return False

        return True

    def _find_inline_customer(self, content):
        """
        Detect customer name embedded inline, e.g. 'لحمضها' → 'حمضها'.
        The 'ل' prefix means 'for' in Arabic.
        """
        # Pattern: "ل" + word at end of a line or content
        match = re.search(r'ل(\S{2,}?)(?:\s|$)', content)
        if match:
            name = match.group(1)
            # Remove possessive suffixes
            for suffix in ['ها', 'هم', 'ه']:
                if name.endswith(suffix) and len(name) > len(suffix) + 1:
                    return name[:-len(suffix)]
            return name
        return None
