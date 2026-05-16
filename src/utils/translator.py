import json
import os
import tkinter as tk

# We import config to get the ACTIVE_LANGUAGE
# If it fails, default to 'ar'
try:
    import config
    ACTIVE_LANGUAGE = getattr(config, 'ACTIVE_LANGUAGE', 'ar')
except ImportError:
    ACTIVE_LANGUAGE = 'ar'

class Translator:
    """Singleton class for managing translations and RTL/LTR logic."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Translator, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
        
    def _init(self):
        self.lang = ACTIVE_LANGUAGE
        self.translations = {}
        self.load_language(self.lang)
        
    def load_language(self, lang):
        """Load translation strings from a JSON file."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locales_path = os.path.join(base_dir, 'locales', f'{lang}.json')
        try:
            if os.path.exists(locales_path):
                with open(locales_path, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                self.lang = lang
            else:
                print(f"Translation file not found: {locales_path}")
                self.translations = {}
        except Exception as e:
            print(f"Error loading translation for {lang}: {e}")
            self.translations = {}
            
    def t(self, key, default=None):
        """Get translated string by key."""
        return self.translations.get(key, default if default is not None else key)
        
    def is_rtl(self):
        """Check if the active language is Right-to-Left."""
        return self.lang == 'ar'
        
    def get_pack_side(self, default=tk.LEFT):
        """Get the correct pack side for LTR/RTL layout logic."""
        if self.is_rtl():
            return tk.RIGHT if default == tk.LEFT else tk.LEFT
        return default

# Global convenience functions
_translator = Translator()

def t(key, default=None):
    return _translator.t(key, default)

def is_rtl():
    return _translator.is_rtl()

def get_pack_side(default=tk.LEFT):
    return _translator.get_pack_side(default)
