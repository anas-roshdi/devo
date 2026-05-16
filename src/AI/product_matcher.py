"""
Smart Product Matcher with Learning System
=============================================
Matches raw Arabic text lines to products in the database using:
1. Learned mappings (from previous user corrections)
2. Fuzzy string matching (difflib)
3. Keyword analysis (كيلو, حبة, صغير, etc.)
"""

import re
import json
import os
from difflib import SequenceMatcher
from dataclasses import dataclass


# Paths
MAPPINGS_FILE = os.path.join(os.path.dirname(__file__), "learned_mappings.json")

# Size keyword mappings
SIZE_KEYWORDS = {
    'صغير': 'S', 'صغيره': 'S', 'صغيرة': 'S', 'small': 'S',
    'كبير': 'L', 'كبيره': 'L', 'كبيرة': 'L', 'large': 'L',
}

# Quantity keywords
HALF_KEYWORDS = ['نص', 'نصف']
PIECE_KEYWORDS = ['حبة', 'حبات', 'حبه']
PIECES_PER_BAG = 10


@dataclass
class MatchResult:
    """Result of matching a text line to a product."""
    product_id: int
    product_name: str
    category: str
    size: str
    quantity: float
    unit_price: float
    confidence: float      # 0.0 - 1.0
    raw_text: str           # Original input text
    ai_product_id: int = 0  # Initial AI prediction
    ai_quantity: float = 0.0 # Initial AI prediction


class ProductMatcher:
    """Matches free-text product descriptions to database products."""

    def __init__(self, db):
        self.db = db
        self.products = []
        self.mappings = {"product_aliases": {}, "customer_names": {}}
        self._load_products()
        self._load_mappings()

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def _load_products(self):
        """Load sellable products from the database."""
        raw = self.db.get_all_products()
        self.products = []
        for p in raw:
            pid, name, category, price, ptype, size = p
            if ptype in ('sellable', 'both'):
                self.products.append({
                    'id': pid, 'name': name, 'category': category or '',
                    'price': price, 'size': size or '',
                })

    def _load_mappings(self):
        """Load learned mappings from JSON file."""
        if os.path.exists(MAPPINGS_FILE):
            try:
                with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
                    self.mappings = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        # Ensure required keys exist
        self.mappings.setdefault("product_aliases", {})
        self.mappings.setdefault("customer_names", {})
        self.mappings.setdefault("exact_matches", {})
        self.mappings.setdefault("stats", {
            "total_customers": 0,
            "correct_customers": 0,
            "total_items": 0,
            "correct_products": 0,
            "correct_quantities": 0
        })

    def save_mappings(self):
        """Persist learned mappings to disk."""
        with open(MAPPINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.mappings, f, ensure_ascii=False, indent=2)

    # ==========================================================
    # MAIN MATCHING API
    # ==========================================================

    def match_line(self, line):
        """
        Match a single product line to the best database product.
        
        Args:
            line: Cleaned text line (e.g. "2 اعواد مموج")
        Returns:
            MatchResult or None if no match found (or if learned to ignore).
        """
        clean_line = self._normalize(line)
        
        # Step 0: Try exact line match first (handles specific quantities and ignored lines)
        exact = self.mappings.get("exact_matches", {}).get(clean_line)
        if exact:
            if exact.get("product_id") == 0:
                return None  # Intentionally ignored
                
            product = self._find_product_by_id(exact.get("product_id"))
            if product:
                return MatchResult(
                    product_id=product['id'],
                    product_name=product['name'],
                    category=product['category'],
                    size=product['size'],
                    quantity=exact.get("quantity", 1),
                    unit_price=product['price'],
                    confidence=1.0,
                    raw_text=line,
                    ai_product_id=product['id'],
                    ai_quantity=exact.get("quantity", 1)
                )

        # Step 1: Extract quantity and clean text
        quantity, is_kilo, is_half_kilo, is_pieces, text_for_match = self._parse_quantity(line)

        # Step 2: Determine size hint
        size_hint = self._extract_size_hint(text_for_match, is_kilo, is_half_kilo)

        # Step 3: Try learned mapping first (highest confidence)
        learned = self._try_learned_mapping(text_for_match, quantity, size_hint)
        if learned:
            return learned

        # Step 4: Fuzzy match against all products
        best = self._fuzzy_match(text_for_match, quantity, size_hint, line)

        # Step 5: Handle حبة conversion (10 pieces = 1 bag)
        if best and is_pieces and quantity >= PIECES_PER_BAG:
            best.quantity = quantity / PIECES_PER_BAG

        if best:
            return best

        # Step 6: Unmatched! Return a dummy MatchResult to be handled in UI
        return MatchResult(
            product_id=0,
            product_name="[Unknown Product]",
            category="",
            size="",
            quantity=quantity,
            unit_price=0.0,
            confidence=0.0,
            raw_text=line,
            ai_product_id=0,
            ai_quantity=0.0
        )

    def match_customer(self, hint, customer_list):
        """
        Match a customer hint text to a customer in the database.
        
        Args:
            hint: Customer name hint 
            customer_list: List of (id, name, phone, ...) tuples from DB
        Returns:
            (customer_id, customer_name) or (1, "General Customer") if not found.
        """
        if not hint:
            return 1, "General Customer"

        # Check learned customer names first
        learned_id = self.mappings.get("customer_names", {}).get(hint)
        if learned_id:
            for c in customer_list:
                if c[0] == learned_id:
                    return c[0], c[1]

        # Fuzzy match against customer names
        best_score = 0
        best_match = None
        for c in customer_list:
            cid, cname = c[0], c[1]
            if cname == "General Customer":
                continue

            # Direct substring check
            if hint in cname or cname in hint:
                return cid, cname

            # Fuzzy similarity
            score = SequenceMatcher(None, hint, cname).ratio()
            if score > best_score:
                best_score = score
                best_match = (cid, cname)

        if best_match and best_score >= 0.6:
            return best_match

        return 1, "General Customer"

    # ==========================================================
    # LEARNING API
    # ==========================================================

    def learn_exact(self, raw_text, product_id, quantity):
        """Learn an exact line mapping, capturing both product and specific quantity."""
        clean = self._normalize(raw_text)
        if clean:
            self.mappings.setdefault("exact_matches", {})
            self.mappings["exact_matches"][clean] = {
                "product_id": product_id,
                "quantity": quantity
            }
            self.save_mappings()

    def learn_product(self, raw_text, product_id):
        """Store a user-confirmed product mapping for future use."""
        # Parse quantity out first to store only the cleaned product alias
        _, _, _, _, text_for_match = self._parse_quantity(raw_text)
        clean = self._normalize(text_for_match)
        if clean and product_id:
            self.mappings["product_aliases"][clean] = product_id
            self.save_mappings()

    def learn_customer(self, name_hint, customer_id):
        """Store a user-confirmed customer mapping for future use."""
        if name_hint and customer_id:
            self.mappings["customer_names"][name_hint] = customer_id
            self.save_mappings()

    # ==========================================================
    # INTERNAL: Quantity & Size Parsing
    # ==========================================================

    def _parse_quantity(self, line):
        """
        Extract quantity and flags from a product line.
        Returns: (quantity, is_kilo, is_half_kilo, is_pieces, remaining_text)
        """
        text = line
        is_kilo = 'كيلو' in text
        is_half_kilo = any(h in text for h in HALF_KEYWORDS) and is_kilo
        is_pieces = any(p in text for p in PIECE_KEYWORDS)

        # Remove quantity-related words for cleaner matching
        for word in HALF_KEYWORDS + PIECE_KEYWORDS + ['كيلو']:
            text = text.replace(word, '')

        # Extract leading number
        match = re.match(r'(\d+(?:\.\d+)?)\s*', text)
        if match:
            quantity = float(match.group(1))
            text = text[match.end():]
        elif is_half_kilo:
            quantity = 1  # "نص كيلو" = 1 unit of half-kilo product
        else:
            quantity = 1  # Default

        return quantity, is_kilo, is_half_kilo, is_pieces, text.strip()

    def _extract_size_hint(self, text, is_kilo, is_half_kilo):
        """Determine the desired product size from keywords."""
        if is_half_kilo:
            return '1/2'
        if is_kilo:
            return '1'

        # Check explicit size keywords (صغير, كبير)
        for keyword, size in SIZE_KEYWORDS.items():
            if keyword in text:
                return size

        return None  # No size preference → use default

    # ==========================================================
    # INTERNAL: Learned Mapping Lookup
    # ==========================================================

    def _try_learned_mapping(self, text, quantity, size_hint):
        """Check if this text was previously mapped by the user."""
        normalized = self._normalize(text)
        aliases = self.mappings.get("product_aliases", {})

        # Try exact match first
        pid = aliases.get(normalized)
        if not pid:
            # Try partial/substring matching in learned aliases
            for alias, alias_pid in aliases.items():
                if alias in normalized or normalized in alias:
                    pid = alias_pid
                    break

        if pid:
            product = self._find_product_by_id(pid, size_hint)
            if product:
                return MatchResult(
                    product_id=product['id'],
                    product_name=product['name'],
                    category=product['category'],
                    size=product['size'],
                    quantity=quantity,
                    unit_price=product['price'],
                    confidence=0.95,
                    raw_text=text,
                    ai_product_id=product['id'],
                    ai_quantity=quantity
                )
        return None

    # ==========================================================
    # INTERNAL: Fuzzy Matching
    # ==========================================================

    def _fuzzy_match(self, text, quantity, size_hint, original_line):
        """Find the best matching product using fuzzy string similarity."""
        normalized = self._normalize(text)
        if not normalized:
            return None

        input_words = set(normalized.split())
        candidates = []

        for p in self.products:
            # Build searchable text from product fields
            p_text = self._normalize(f"{p['name']} {p['category']}")
            p_name_norm = self._normalize(p['name'])
            product_words = set(p_text.split())

            # Calculate base similarity score
            base_score = SequenceMatcher(None, normalized, p_text).ratio()
            score = base_score

            # Bonus: keyword overlap (shared words)
            overlap = input_words & product_words
            if overlap:
                score += (len(overlap) / max(len(input_words), len(product_words))) * 0.3

            # Strong bonus: if an input word IS a product name (direct match)
            for word in input_words:
                if word == p_name_norm:
                    score += 0.4
                elif len(word) > 2 and word in p_name_norm:
                    score += 0.1

            # Bonus/Penalty: "كيلو" alignment with "بالكيلو" products
            if 'كيلو' in original_line and p['name'].startswith('بالكيلو'):
                score += 0.3
            elif 'كيلو' not in original_line and p['name'].startswith('بالكيلو'):
                score -= 0.3

            # Size preference
            if size_hint and p['size'] == size_hint:
                score += 0.2
            elif size_hint and p['size'] != size_hint:
                score -= 0.1
            
            # Default size: if no size hint, prefer S (user's default)
            if not size_hint and p['size'] == 'S':
                score += 0.05

            candidates.append((p, score))

        if not candidates:
            return None

        # Sort by score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_product, best_score = candidates[0]

        # Clamp confidence to 0-1 range
        confidence = min(max(best_score, 0.0), 1.0)
        
        # Prevent 100% confidence unless it's a very exact match
        best_p_text = self._normalize(f"{best_product['name']} {best_product['category']}")
        base_best_score = SequenceMatcher(None, normalized, best_p_text).ratio()
        if base_best_score < 0.95 and confidence >= 1.0:
            confidence = 0.95

        if confidence < 0.2:
            return None

        return MatchResult(
            product_id=best_product['id'],
            product_name=best_product['name'],
            category=best_product['category'],
            size=best_product['size'],
            quantity=quantity,
            unit_price=best_product['price'],
            confidence=round(confidence, 2),
            raw_text=text,
            ai_product_id=best_product['id'],
            ai_quantity=quantity
        )

    # ==========================================================
    # INTERNAL: Helpers
    # ==========================================================

    def _find_product_by_id(self, pid, size_hint=None):
        """Find a product by ID, optionally filtering by size."""
        # First try exact ID match
        exact = [p for p in self.products if p['id'] == pid]
        if exact:
            return exact[0]

        # If size_hint, find same-name product with that size
        if size_hint:
            base = [p for p in self.products if p['id'] == pid]
            if base:
                name = base[0]['name']
                sized = [p for p in self.products if p['name'] == name and p['size'] == size_hint]
                if sized:
                    return sized[0]

        return None

    @staticmethod
    def _normalize(text):
        """Normalize Arabic text for comparison: remove diacritics, extra spaces."""
        if not text:
            return ''
        # Remove Arabic diacritics (tashkeel)
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)
        # Normalize common letter variations
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
