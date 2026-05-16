"""
AI Sales Entry Window
========================
Independent window for parsing WhatsApp messages into sales invoices
using the AI engine. Supports review, editing, and batch confirmation.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from src.AI.invoice_extractor import InvoiceExtractor
from src.database.database_manager import DatabaseManager
from config import Colors, Fonts, WindowConfig, DEFAULT_CUSTOMER
from src.utils.translator import t, get_pack_side, is_rtl


class AISalesWindow:
    """AI-powered WhatsApp to Invoice converter with review interface."""

    def __init__(self, root):
        self.root = root
        self.root.title(t('ai_win_title'))

        geo, min_w, min_h = WindowConfig.AI_SALES
        self.root.geometry(geo)
        self.root.minsize(min_w, min_h)

        # AI Engine
        self.extractor = InvoiceExtractor()
        self.db = DatabaseManager()

        # State
        self.parsed_invoices = []
        self.current_index = -1
        self.confirmed_count = 0

        # Load customer/product data for editing
        self.customers = self.db.get_all_customers()
        self.customer_names = [c[1] for c in self.customers]
        self.customer_map = {c[1]: c[0] for c in self.customers}

        products = self.db.get_all_products()
        self.product_display_map = {}
        self.product_price_map = {}
        self.product_list = []
        for p in products:
            pid, name, cat, price, ptype, size = p
            if ptype in ('sellable', 'both'):
                self.product_price_map[pid] = price
                display = f"{name}"
                if cat and str(cat).strip():
                    display += f" ({cat})"
                if size and str(size).strip():
                    display += f" [{size}]"
                self.product_display_map[display] = {
                    'id': pid, 
                    'price': price,
                    'name': name,
                    'category': cat or '',
                    'size': size or ''
                }
                self.product_list.append(display)

        self.create_widgets()

    # ==========================================================
    # UI CONSTRUCTION
    # ==========================================================

    def create_widgets(self):
        """Build the three-section interface."""

        # ── SECTION 1: Input Area ──
        input_frame = tk.LabelFrame(self.root, text=t('lbl_paste_messages'),
                                    padx=10, pady=10, font=Fonts.LABEL_FRAME)
        input_frame.pack(fill="x", padx=15, pady=(10, 5))

        # Top row: Year selector + Parse button
        top_row = tk.Frame(input_frame)
        top_row.pack(fill="x", pady=(0, 5))

        tk.Label(top_row, text=t('lbl_year')).pack(side=get_pack_side(tk.LEFT))
        self.spin_year = tk.Spinbox(top_row, from_=2024, to=2030, width=6,
                                    value=datetime.now().year)
        self.spin_year.pack(side=get_pack_side(tk.LEFT), padx=5)

        tk.Button(top_row, text=t('btn_parse_ai'), bg=Colors.PURPLE,
                  fg=Colors.TEXT_WHITE, font=Fonts.BTN_MEDIUM,
                  command=self.parse_messages).pack(side=get_pack_side(tk.RIGHT))

        tk.Button(top_row, text=t('btn_clear'), bg=Colors.GRAY, fg=Colors.TEXT_WHITE,
                  command=self.clear_all).pack(side=get_pack_side(tk.RIGHT), padx=5)

        # Text area
        self.txt_input = scrolledtext.ScrolledText(input_frame, height=6,
                                                    font=("Courier New", 10),
                                                    wrap=tk.WORD)
        self.txt_input.pack(fill="x")
        
        # Explicit paste bindings to support Arabic keyboard layouts
        def handle_paste(event):
            try:
                text = self.root.clipboard_get()
                self.txt_input.insert(tk.INSERT, text)
            except tk.TclError:
                pass
            return "break"
            
        self.txt_input.bind("<Control-v>", handle_paste)
        self.txt_input.bind("<Control-V>", handle_paste)
        
        # Handle Arabic keyboard layouts by checking keycode (V is 86 on Windows)
        def handle_arabic_paste(event):
            if event.state & 4 and event.keycode == 86: # Control + V key
                return handle_paste(event)
                
        self.txt_input.bind("<KeyPress>", handle_arabic_paste)

        # ── SECTION 2: Results Area ──
        results_frame = tk.Frame(self.root)
        results_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Left: Invoice list
        left_frame = tk.LabelFrame(results_frame, text=t('lbl_invoices_found'),
                                   font=Fonts.LABEL_FRAME, width=250)
        left_frame.pack(side=get_pack_side(tk.LEFT), fill="y", padx=(0, 5))
        left_frame.pack_propagate(False)

        self.invoice_listbox = tk.Listbox(left_frame, font=Fonts.BODY,
                                          activestyle="none",
                                          selectbackground=Colors.BLUE,
                                          exportselection=False)
        self.invoice_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.invoice_listbox.bind("<<ListboxSelect>>", self.on_invoice_select)

        # Right: Invoice details
        right_frame = tk.LabelFrame(results_frame, text=t('lbl_invoice_details'),
                                    font=Fonts.LABEL_FRAME)
        right_frame.pack(side=get_pack_side(tk.LEFT), fill="both", expand=True)

        # Customer + Date row
        detail_header = tk.Frame(right_frame)
        detail_header.pack(fill="x", padx=10, pady=5)

        tk.Label(detail_header, text=t('lbl_customer')).pack(side=get_pack_side(tk.LEFT))
        self.combo_customer = ttk.Combobox(detail_header, values=self.customer_names,
                                           state="readonly", width=20)
        self.combo_customer.pack(side=get_pack_side(tk.LEFT), padx=5)
        self.combo_customer.bind("<<ComboboxSelected>>", self.on_customer_change)

        tk.Label(detail_header, text=t('lbl_date')).pack(side=get_pack_side(tk.LEFT), padx=(15, 0))
        self.ent_date = tk.Entry(detail_header, width=12)
        self.ent_date.pack(side=get_pack_side(tk.LEFT), padx=5)

        # Original text display
        self.lbl_original = tk.Label(right_frame, text="", fg=Colors.GRAY,
                                     font=("Arial", 9, "italic"), wraplength=500,
                                     justify=get_pack_side(tk.RIGHT), anchor="e")
        self.lbl_original.pack(fill="x", padx=10)

        # Items table
        table_frame = tk.Frame(right_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = (t('col_raw_text'), t('col_product'), t('col_qty'), t('col_price'), t('col_subtotal'), t('col_confidence'))
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                 height=6, selectmode="browse")
        col_widths = {"Raw Text": 140, "Product": 160, "Qty": 50,
                      "Price": 60, "Subtotal": 70, "Confidence": 70}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor="center")

        self.tree.pack(side=get_pack_side(tk.LEFT), fill="both", expand=True)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=get_pack_side(tk.RIGHT), fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

        # Edit row (shown when item is selected)
        edit_frame = tk.LabelFrame(right_frame, text=t('lbl_edit_item'),
                                   padx=5, pady=5)
        edit_frame.pack(fill="x", padx=10, pady=(0, 5))

        tk.Label(edit_frame, text=t('lbl_product')).grid(row=0, column=0)
        self.combo_edit_product = ttk.Combobox(edit_frame, values=self.product_list,
                                                width=30)
        self.combo_edit_product.grid(row=0, column=1, padx=5)
        self.combo_edit_product.bind("<<ComboboxSelected>>", self.on_edit_product_change)

        tk.Label(edit_frame, text=t('lbl_qty')).grid(row=0, column=2)
        self.ent_edit_qty = tk.Entry(edit_frame, width=6)
        self.ent_edit_qty.grid(row=0, column=3, padx=5)

        tk.Label(edit_frame, text=t('lbl_price')).grid(row=0, column=4)
        self.ent_edit_price = tk.Entry(edit_frame, width=8)
        self.ent_edit_price.grid(row=0, column=5, padx=5)

        tk.Button(edit_frame, text=t('btn_update'), bg=Colors.ORANGE,
                  command=self.update_item).grid(row=0, column=6, padx=5)

        tk.Button(edit_frame, text=t('btn_add'), bg=Colors.BLUE, fg=Colors.TEXT_WHITE,
                  command=self.add_item).grid(row=0, column=7, padx=5)

        tk.Button(edit_frame, text=t('btn_delete'), bg=Colors.RED, fg=Colors.TEXT_WHITE,
                  command=self.delete_item).grid(row=0, column=8, padx=5)

        # ── SECTION 3: Action Buttons ──
        action_frame = tk.Frame(self.root, padx=15, pady=10)
        action_frame.pack(fill="x")

        tk.Button(action_frame, text=t('btn_confirm_current'),
                  bg=Colors.GREEN_DARK, fg=Colors.TEXT_WHITE,
                  font=Fonts.BTN_MEDIUM, command=self.confirm_current).pack(
                      side=get_pack_side(tk.LEFT), padx=5)

        tk.Button(action_frame, text=t('btn_confirm_all'),
                  bg=Colors.GREEN, fg=Colors.TEXT_WHITE,
                  font=Fonts.BTN_MEDIUM, command=self.confirm_all).pack(
                      side=get_pack_side(tk.LEFT), padx=5)

        tk.Button(action_frame, text=t('btn_skip_current'),
                  bg=Colors.RED, fg=Colors.TEXT_WHITE,
                  command=self.skip_current).pack(side=get_pack_side(tk.LEFT), padx=5)

        self.lbl_progress = tk.Label(action_frame, text=t('lbl_no_invoices'),
                                     font=Fonts.BODY_BOLD, fg=Colors.PRIMARY_DARK)
        self.lbl_progress.pack(side=get_pack_side(tk.RIGHT))
        
        self.lbl_accuracy = tk.Label(action_frame, text=t('lbl_accuracy_na'),
                                     font=Fonts.BODY_BOLD, fg=Colors.PURPLE)
        self.lbl_accuracy.pack(side=get_pack_side(tk.RIGHT), padx=15)
        
        self._update_accuracy_label()

    # ==========================================================
    # PARSE ACTION
    # ==========================================================

    def parse_messages(self):
        """Parse the pasted WhatsApp text using AI engine."""
        raw = self.txt_input.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning(t('msg_empty_title'), t('msg_paste_first'))
            return

        # Set year
        try:
            year = int(self.spin_year.get())
        except ValueError:
            year = datetime.now().year
        self.extractor.set_year(year)

        # Parse
        self.parsed_invoices = self.extractor.extract(raw)
        self.confirmed_count = 0

        if not self.parsed_invoices:
            messagebox.showinfo(t('msg_no_results'),
                                t('msg_no_invoices_found'))
            return

        # Apply smart pricing based on recognized customer names
        for inv in self.parsed_invoices:
            self._apply_smart_pricing(inv)

        # Populate invoice list
        self.invoice_listbox.delete(0, tk.END)
        for i, inv in enumerate(self.parsed_invoices):
            status = "✅" if inv.confirmed else "📄"
            label = f"{status} {inv.date} | {inv.customer_name} | {len(inv.items)} items"
            self.invoice_listbox.insert(tk.END, label)

        self._update_progress()

        # Select first invoice
        self.invoice_listbox.selection_set(0)
        self.on_invoice_select(None)

        messagebox.showinfo(t('msg_parsed_title'),
                            t('msg_parsed_body').format(count=len(self.parsed_invoices)))

    # ==========================================================
    # INVOICE NAVIGATION
    # ==========================================================

    def on_invoice_select(self, event):
        """Display the selected invoice's details."""
        sel = self.invoice_listbox.curselection()
        if not sel:
            return

        self.current_index = sel[0]
        inv = self.parsed_invoices[self.current_index]

        # Update customer and date
        self.combo_customer.set(inv.customer_name)
        self.ent_date.delete(0, tk.END)
        self.ent_date.insert(0, inv.date)

        # Show original text
        self.lbl_original.config(text=t('lbl_original_text').format(text=inv.raw_text[:120]))

        # Populate items table
        self.tree.delete(*self.tree.get_children())
        for item in inv.items:
            conf_str = f"{item.confidence:.0%}"
            product_display = f"{item.product_name}"
            if item.category:
                product_display += f" ({item.category})"
            if item.size:
                product_display += f" [{item.size}]"

            tag = self._confidence_tag(item.confidence)
            self.tree.insert("", tk.END, values=(
                item.raw_text, product_display,
                item.quantity, f"{item.unit_price:.2f}",
                f"{item.subtotal:.2f}", conf_str
            ), tags=(tag,))

        # Apply tag colors
        self.tree.tag_configure("high", background="#d4edda")
        self.tree.tag_configure("medium", background="#fff3cd")
        self.tree.tag_configure("low", background="#f8d7da")

    def on_item_select(self, event):
        """Populate edit fields when a table row is selected."""
        sel = self.tree.selection()
        if not sel:
            return

        values = self.tree.item(sel[0], "values")
        # Try to find the matching product in the combobox list
        product_text = values[1]

        # Set edit fields
        self.combo_edit_product.set(product_text)
        self.ent_edit_qty.delete(0, tk.END)
        self.ent_edit_qty.insert(0, values[2])
        self.ent_edit_price.delete(0, tk.END)
        self.ent_edit_price.insert(0, values[3])

    def on_edit_product_change(self, event):
        """Auto-fill price when edit product is changed."""
        display = self.combo_edit_product.get()
        if display in self.product_display_map:
            price = self.product_display_map[display]['price']
            self.ent_edit_price.delete(0, tk.END)
            self.ent_edit_price.insert(0, f"{price:.2f}")

    def on_customer_change(self, event=None):
        """Handle customer selection change: update invoice and apply smart pricing."""
        if self.current_index < 0:
            return
        inv = self.parsed_invoices[self.current_index]
        new_name = self.combo_customer.get()
        if new_name != inv.customer_name:
            inv.customer_name = new_name
            self._apply_smart_pricing(inv)
            # Refresh the display with new prices
            self.on_invoice_select(None)

    def _apply_smart_pricing(self, inv):
        """Update item prices based on the customer's last purchase."""
        cust_id = self.customer_map.get(inv.customer_name, 1)
        
        for item in inv.items:
            # 1. Reset to the database default price for this product
            default_price = self.product_price_map.get(item.product_id, item.unit_price)
            final_price = default_price
            
            # 2. If it's a specific customer, try to fetch their last price
            if cust_id != 1:
                last_price = self.db.get_last_sale_price(cust_id, item.product_id)
                if last_price is not None:
                    final_price = last_price
            
            # 3. Update the item
            item.unit_price = final_price
            item.subtotal = final_price * item.quantity
            
        # Update the invoice total
        inv.total = sum(i.subtotal for i in inv.items)

    # ==========================================================
    # EDIT ITEM
    # ==========================================================

    def update_item(self):
        """Apply edits to the selected item in the current invoice."""
        sel = self.tree.selection()
        if not sel or self.current_index < 0:
            return

        idx = self.tree.index(sel[0])
        inv = self.parsed_invoices[self.current_index]
        item = inv.items[idx]

        # Get new values
        product_display = self.combo_edit_product.get()
        try:
            new_qty = float(self.ent_edit_qty.get())
            new_price = float(self.ent_edit_price.get())
        except ValueError:
            messagebox.showerror(t('msg_error_title'), t('msg_numbers_req'))
            return

        # Find product ID and details from display
        if product_display in self.product_display_map:
            p_info = self.product_display_map[product_display]
            new_pid = p_info['id']
            item.product_name = p_info['name']
            item.category = p_info['category']
            item.size = p_info['size']
        else:
            new_pid = item.product_id
            parts = product_display.split(" (")
            item.product_name = parts[0] if parts else product_display

        # Update the item
        item.product_id = new_pid
        item.quantity = new_qty
        item.unit_price = new_price
        item.subtotal = new_qty * new_price

        # Update invoice total
        inv.total = sum(it.subtotal for it in inv.items)

        # Refresh display
        self.on_invoice_select(None)

    def add_item(self):
        """Add a new item manually to the current invoice."""
        if self.current_index < 0:
            return
            
        inv = self.parsed_invoices[self.current_index]
        product_display = self.combo_edit_product.get()
        
        if not product_display or product_display not in self.product_display_map:
            messagebox.showwarning(t('msg_warning_title'), t('msg_select_valid_product'))
            return
            
        try:
            qty = float(self.ent_edit_qty.get())
            price = float(self.ent_edit_price.get())
        except ValueError:
            messagebox.showerror(t('msg_error_title'), t('msg_numbers_req'))
            return
            
        p_info = self.product_display_map[product_display]
        pid = p_info['id']
        p_name = p_info['name']
        p_cat = p_info['category']
        p_size = p_info['size']
        
        from src.AI.invoice_extractor import ParsedItem
        new_item = ParsedItem(
            product_id=pid,
            product_name=p_name,
            category=p_cat,
            size=p_size,
            quantity=qty,
            unit_price=price,
            subtotal=qty * price,
            confidence=1.0, # 100% since manually added
            raw_text="[Added Manually]",
            ai_product_id=pid,
            ai_quantity=qty
        )
        # Calculate subtotal directly here
        new_item.subtotal = qty * price
        
        inv.items.append(new_item)
        inv.total = sum(it.subtotal for it in inv.items)
        self.on_invoice_select(None)

    def delete_item(self):
        """Delete the selected item from the current invoice."""
        sel = self.tree.selection()
        if not sel or self.current_index < 0:
            return
            
        idx = self.tree.index(sel[0])
        inv = self.parsed_invoices[self.current_index]
        
        if messagebox.askyesno(t('msg_confirm_title'), t('msg_remove_item_confirm')):
            deleted_item = inv.items.pop(idx)
            if hasattr(inv, 'deleted_lines'):
                inv.deleted_lines.append(deleted_item.raw_text)
                
            inv.total = sum(it.subtotal for it in inv.items)
            self.on_invoice_select(None)

    # ==========================================================
    # CONFIRM / SKIP
    # ==========================================================

    def confirm_current(self):
        """Confirm and save the currently selected invoice."""
        if self.current_index < 0:
            return

        inv = self.parsed_invoices[self.current_index]
        if inv.confirmed:
            messagebox.showinfo(t('msg_info_title'), t('msg_already_confirmed'))
            return

        # Get final customer
        cust_name = self.combo_customer.get()
        cust_id = self.customer_map.get(cust_name, 1)

        # Get final date
        inv.date = self.ent_date.get()

        # Build items for database
        final_items = []
        for item in inv.items:
            if item.product_id == 0:
                messagebox.showerror(t('msg_error_title'), t('msg_resolve_items'))
                return
            final_items.append({
                'id': item.product_id,
                'qty': item.quantity,
                'price': item.unit_price,
                'subtotal': item.subtotal,
            })

        try:
            inv_id = self.extractor.confirm_invoice(inv, cust_id, final_items)
            inv.confirmed = True
            inv.customer_id = cust_id
            inv.customer_name = cust_name
            self.confirmed_count += 1

            # Update listbox label
            label = f"✅ {inv.date} | {cust_name} | {len(inv.items)} items"
            self.invoice_listbox.delete(self.current_index)
            self.invoice_listbox.insert(self.current_index, label)

            self._update_progress()
            self._select_next_unconfirmed()

            messagebox.showinfo(t('msg_success_title'), t('msg_invoice_saved_short').format(inv_id=inv_id))
        except Exception as e:
            messagebox.showerror(t('msg_error_title'), t('msg_failed_save').format(e=e))

    def confirm_all(self):
        """Confirm all remaining unconfirmed invoices."""
        remaining = [i for i, inv in enumerate(self.parsed_invoices)
                     if not inv.confirmed]

        if not remaining:
            messagebox.showinfo(t('msg_done_title'), t('msg_all_confirmed'))
            return

        if not messagebox.askyesno(t('msg_confirm_all_title'),
                                    t('msg_confirm_all_body').format(count=len(remaining))):
            return

        saved = 0
        for idx in remaining:
            self.current_index = idx
            inv = self.parsed_invoices[idx]
            cust_id = inv.customer_id

            if any(item.product_id == 0 for item in inv.items):
                messagebox.showerror(t('msg_error_title'), t('msg_skip_unresolved').format(name=inv.customer_name))
                continue

            final_items = [{
                'id': item.product_id,
                'qty': item.quantity,
                'price': item.unit_price,
                'subtotal': item.subtotal,
            } for item in inv.items]

            try:
                self.extractor.confirm_invoice(inv, cust_id, final_items)
                inv.confirmed = True
                self.confirmed_count += 1
                saved += 1

                label = f"✅ {inv.date} | {inv.customer_name} | {len(inv.items)} items"
                self.invoice_listbox.delete(idx)
                self.invoice_listbox.insert(idx, label)
            except Exception:
                continue

        self._update_progress()
        messagebox.showinfo(t('msg_done_title'), t('msg_confirmed_all_success').format(count=saved))

    def skip_current(self):
        """Skip the current invoice and delete it."""
        if self.current_index < 0:
            return
            
        if messagebox.askyesno(t('msg_confirm_title'), t('msg_delete_invoice_confirm')):
            self.parsed_invoices.pop(self.current_index)
            self.invoice_listbox.delete(self.current_index)
            
            if not self.parsed_invoices:
                self.clear_all()
            else:
                self._update_progress()
                # Try to select next unconfirmed
                found = False
                for i, inv in enumerate(self.parsed_invoices):
                    if not inv.confirmed:
                        self.invoice_listbox.selection_clear(0, tk.END)
                        self.invoice_listbox.selection_set(i)
                        self.invoice_listbox.see(i)
                        self.on_invoice_select(None)
                        found = True
                        break
                
                # If all confirmed, just select the first one
                if not found and self.parsed_invoices:
                    self.invoice_listbox.selection_clear(0, tk.END)
                    self.invoice_listbox.selection_set(0)
                    self.invoice_listbox.see(0)
                    self.on_invoice_select(None)

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _update_progress(self):
        """Update the progress label."""
        total = len(self.parsed_invoices)
        self.lbl_progress.config(
            text=t('lbl_confirmed_progress').format(confirmed=self.confirmed_count, total=total)
        )
        self._update_accuracy_label()

    def _update_accuracy_label(self):
        """Update the AI accuracy statistics label."""
        stats = self.extractor.matcher.mappings.get("stats", {})
        total_eval = stats.get("total_customers", 0) + (stats.get("total_items", 0) * 2)
        if total_eval == 0:
            self.lbl_accuracy.config(text=t('lbl_accuracy_na'))
            return
            
        correct = (stats.get("correct_customers", 0) + 
                   stats.get("correct_products", 0) + 
                   stats.get("correct_quantities", 0))
                   
        accuracy = (correct / total_eval) * 100
        self.lbl_accuracy.config(text=t('lbl_accuracy_value').format(accuracy=accuracy))

    def _select_next_unconfirmed(self):
        """Select the next unconfirmed invoice in the list."""
        for i, inv in enumerate(self.parsed_invoices):
            if not inv.confirmed:
                self.invoice_listbox.selection_clear(0, tk.END)
                self.invoice_listbox.selection_set(i)
                self.invoice_listbox.see(i)
                self.on_invoice_select(None)
                return

    @staticmethod
    def _confidence_tag(confidence):
        """Return a tag name based on confidence level."""
        if confidence >= 0.7:
            return "high"
        elif confidence >= 0.4:
            return "medium"
        return "low"

    def clear_all(self):
        """Reset the entire interface."""
        self.txt_input.delete("1.0", tk.END)
        self.invoice_listbox.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self.parsed_invoices = []
        self.current_index = -1
        self.confirmed_count = 0
        self.combo_customer.set("")
        self.ent_date.delete(0, tk.END)
        self.lbl_original.config(text="")
        self._update_progress()


if __name__ == "__main__":
    root = tk.Tk()
    app = AISalesWindow(root)
    root.mainloop()
