import tkinter as tk
from tkcalendar import Calendar
from datetime import datetime

class CalendarHelper:
    @staticmethod
    def show_calendar(parent, target_entry):
        """
        Opens a popup calendar and updates the target entry field.
        :param parent: The root or top-level window.
        :param target_entry: The tkinter Entry widget to be updated.
        """
        # Create a popup window
        top = tk.Toplevel(parent)
        top.title("Select Date")
        top.geometry("300x280")
        
        # Keep window on top and modal
        top.grab_set()

        # Calendar widget setup
        cal = Calendar(top, selectmode='day', 
                       date_pattern='yyyy-mm-dd',
                       year=datetime.now().year, 
                       month=datetime.now().month)
        cal.pack(fill="both", expand=True, padx=10, pady=10)

        def on_date_select(event=None):
            """Update the specific target entry and close the popup."""
            target_entry.delete(0, tk.END)
            target_entry.insert(0, cal.get_date())
            top.destroy()

        # Bind the selection event
        cal.bind("<<CalendarSelected>>", on_date_select)