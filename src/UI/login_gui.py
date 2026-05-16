import tkinter as tk
from tkinter import messagebox
from src.database.database_manager import DatabaseManager
from config import Colors, Fonts
from src.utils.translator import t

class LoginScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(t('login_title', default='Devo - Login'))
        
        # Center the window
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.configure(bg=Colors.BACKGROUND)
        self.root.resizable(False, False)
        
        self.db = DatabaseManager()
        self.authenticated_role = None
        
        # Override window close event to ensure we can exit if not logged in
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header frame
        header_frame = tk.Frame(self.root, bg=Colors.PRIMARY_DARK, height=60)
        header_frame.pack(fill="x", pady=(0, 20))
        tk.Label(
            header_frame, 
            text=t('login_header', default='System Login'), 
            fg=Colors.TEXT_WHITE, 
            bg=Colors.PRIMARY_DARK, 
            font=Fonts.HEADER_LARGE
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # Main form frame
        form_frame = tk.Frame(self.root, bg=Colors.BACKGROUND)
        form_frame.pack(pady=10)
        
        # Username input
        tk.Label(
            form_frame, 
            text=t('lbl_username', default='Username:'), 
            bg=Colors.BACKGROUND, 
            font=Fonts.BODY
        ).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        self.username_var = tk.StringVar()
        tk.Entry(
            form_frame, 
            textvariable=self.username_var, 
            font=Fonts.BODY, 
            width=20
        ).grid(row=0, column=1, padx=10, pady=10)
        
        # Password input
        tk.Label(
            form_frame, 
            text=t('lbl_password', default='Password:'), 
            bg=Colors.BACKGROUND, 
            font=Fonts.BODY
        ).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        self.password_var = tk.StringVar()
        tk.Entry(
            form_frame, 
            textvariable=self.password_var, 
            font=Fonts.BODY, 
            width=20, 
            show='*'  # Hide characters
        ).grid(row=1, column=1, padx=10, pady=10)
        
        # Login Button
        tk.Button(
            self.root, 
            text=t('btn_login', default='Login'), 
            bg=Colors.BLUE, 
            fg=Colors.TEXT_WHITE,
            font=Fonts.BODY_BOLD, 
            width=15, 
            command=self.attempt_login
        ).pack(pady=20)
                  
        # Bind Enter key to login
        self.root.bind('<Return>', lambda event: self.attempt_login())
        
    def attempt_login(self):
        """Verify the credentials against the database."""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showwarning(
                t('msg_warning_title', default='Warning'), 
                t('msg_login_empty', default='Please enter username and password.')
            )
            return
            
        role = self.db.authenticate_user(username, password)
        if role:
            # Login successful
            self.authenticated_role = role
            self.root.destroy()
        else:
            # Login failed
            messagebox.showerror(
                t('msg_error_title', default='Error'), 
                t('msg_login_failed', default='Invalid username or password.')
            )
            
    def on_close(self):
        """Handle window close event without logging in."""
        self.authenticated_role = None
        self.root.destroy()
        
    def run(self):
        """Run the login window loop and return the authenticated role."""
        self.root.mainloop()
        return self.authenticated_role
