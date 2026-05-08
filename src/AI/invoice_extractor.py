"""
Invoice Extractor - Main Orchestrator
========================================
Combines WhatsAppParser + ProductMatcher to convert raw WhatsApp text
into structured invoice objects ready for user review.
"""

from dataclasses import dataclass, field
from src.AI.whatsapp_parser import WhatsAppParser
from src.AI.product_matcher import ProductMatcher, MatchResult
from src.database.database_manager import DatabaseManager


@dataclass
class ParsedItem:
    """A single item in a parsed invoice."""
    raw_text: str
    product_id: int
    product_name: str
    category: str
    size: str
    quantity: float
    unit_price: float
    subtotal: float
    confidence: float
    ai_product_id: int = 0
    ai_quantity: float = 0.0


@dataclass
class ParsedInvoice:
    """A complete parsed invoice ready for user review."""
    date: str
    customer_id: int
    customer_name: str
    customer_hint: str          # Original detected hint
    items: list                 # List of ParsedItem
    raw_text: str               # Original WhatsApp message
    total: float = 0.0
    confirmed: bool = False     # User has reviewed and approved
    ai_customer_id: int = 0
    deleted_lines: list = field(default_factory=list) # Lines the user deleted


class InvoiceExtractor:
    """
    Main orchestrator: takes raw WhatsApp text and produces
    a list of ParsedInvoice objects for user review.
    """

    def __init__(self):
        self.db = DatabaseManager()
        self.parser = WhatsAppParser()
        self.matcher = ProductMatcher(self.db)
        self._customer_list = None

    def set_year(self, year):
        """Set the year for date parsing (WhatsApp dates lack year)."""
        self.parser.year = year

    @property
    def customer_list(self):
        """Lazy-load customer list from database."""
        if self._customer_list is None:
            self._customer_list = self.db.get_all_customers()
        return self._customer_list

    # ==========================================================
    # MAIN API
    # ==========================================================

    def extract(self, raw_text):
        """
        Parse WhatsApp text and produce invoice objects.
        
        Args:
            raw_text: Full pasted WhatsApp chat export.
        Returns:
            List of ParsedInvoice objects.
        """
        # Step 1: Parse WhatsApp messages into blocks
        blocks = self.parser.parse(raw_text)

        # Step 2: Convert each block into a ParsedInvoice
        invoices = []
        for block in blocks:
            invoice = self._process_block(block)
            if invoice and invoice.items:
                invoices.append(invoice)

        return invoices

    def confirm_invoice(self, invoice, final_customer_id, final_items):
        """
        Save a confirmed invoice to the database and learn from corrections.
        
        Args:
            invoice: The original ParsedInvoice
            final_customer_id: User-confirmed customer ID
            final_items: List of dicts with keys: id, qty, price, subtotal
        Returns:
            The saved invoice ID.
        """
        total = sum(item['subtotal'] for item in final_items)

        # Save to database
        invoice_id = self.db.save_sale_invoice(
            final_customer_id, invoice.date, total, final_items
        )

        # Learn from this confirmation
        self._learn_from_confirmation(invoice, final_customer_id, final_items)

        invoice.confirmed = True
        return invoice_id

    # ==========================================================
    # INTERNAL: Block Processing
    # ==========================================================

    def _process_block(self, block):
        """Convert a MessageBlock into a ParsedInvoice."""
        # Match customer
        cust_id, cust_name = self.matcher.match_customer(
            block.customer_hint, self.customer_list
        )

        # Match each product line
        items = []
        for line in block.content_lines:
            match = self.matcher.match_line(line)
            if match:
                items.append(ParsedItem(
                    raw_text=line,
                    product_id=match.product_id,
                    product_name=match.product_name,
                    category=match.category,
                    size=match.size,
                    quantity=match.quantity,
                    unit_price=match.unit_price,
                    subtotal=match.quantity * match.unit_price,
                    confidence=match.confidence,
                    ai_product_id=match.ai_product_id,
                    ai_quantity=match.ai_quantity,
                ))

        if not items:
            return None

        total = sum(item.subtotal for item in items)

        return ParsedInvoice(
            date=block.date,
            customer_id=cust_id,
            customer_name=cust_name,
            customer_hint=block.customer_hint or "",
            items=items,
            raw_text=block.raw_text,
            total=total,
            ai_customer_id=cust_id,
            deleted_lines=[]
        )

    # ==========================================================
    # INTERNAL: Learning
    # ==========================================================

    def _learn_from_confirmation(self, invoice, final_customer_id, final_items):
        """
        After user confirms an invoice, learn the correct mappings
        so future parsing is more accurate.
        """
        stats = self.matcher.mappings.setdefault("stats", {
            "total_customers": 0, "correct_customers": 0,
            "total_items": 0, "correct_products": 0, "correct_quantities": 0
        })

        # Track customer accuracy
        stats["total_customers"] += 1
        if invoice.ai_customer_id == final_customer_id:
            stats["correct_customers"] += 1

        # Learn customer mapping
        if invoice.customer_hint:
            self.matcher.learn_customer(invoice.customer_hint, final_customer_id)

        # Ensure exact_matches dict exists
        self.matcher.mappings.setdefault("exact_matches", {})

        # Learn deleted lines (ignored)
        for raw_text in invoice.deleted_lines:
            if raw_text != "[Added Manually]":
                self.matcher.learn_exact(raw_text, 0, 0)

        # Learn product mappings and track item accuracy
        for item in invoice.items:
            if item.raw_text == "[Added Manually]":
                continue
                
            stats["total_items"] += 1
            
            # Learn EXACT mapping (includes specific quantity)
            self.matcher.learn_exact(item.raw_text, item.product_id, item.quantity)
            
            # item.product_id is the final state, item.ai_product_id is original
            if item.ai_product_id == item.product_id:
                stats["correct_products"] += 1
            else:
                self.matcher.learn_product(item.raw_text, item.product_id)
                
            if item.ai_quantity == item.quantity:
                stats["correct_quantities"] += 1
                
            # Reinforce the general mapping
            if item.ai_product_id == item.product_id:
                self.matcher.learn_product(item.raw_text, item.product_id)
                
        self.matcher.save_mappings()

    def reload(self):
        """Reload products and customers (after DB changes)."""
        self._customer_list = None
        self.matcher._load_products()
        self.matcher._load_mappings()
