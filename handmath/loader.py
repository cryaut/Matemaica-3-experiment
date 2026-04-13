import os
import xml.etree.ElementTree as ET

class SymbolVariant:
    def __init__(self, filepath):
        self.filepath = filepath
        self.tree = ET.parse(filepath)
        self.root = self.tree.getroot()
        
        # Strip namespaces for easier processing and clean output
        for elem in self.root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]
                
        self.width = self._parse_length(self.root.attrib.get('width', '50'))
        self.height = self._parse_length(self.root.attrib.get('height', '50'))
        
        # Prefer viewBox for accurate dimensions if available
        viewbox = self.root.attrib.get('viewBox')
        if viewbox:
            parts = list(map(float, viewbox.replace(',', ' ').split()))
            if len(parts) == 4:
                self.width = parts[2]
                self.height = parts[3]
                
        # Extract inner elements (ignore metadata tags)
        self.elements = [child for child in self.root if child.tag not in ('defs', 'metadata', 'title', 'desc')]

    def _parse_length(self, val):
        if isinstance(val, str):
            val = val.replace('px', '').replace('pt', '').replace('em', '')
            try:
                return float(val)
            except ValueError:
                return 50.0
        return float(val)

class SymbolLoader:
    def __init__(self, symbols_dir: str):
        self.symbols_dir = symbols_dir
        self.symbols = {} # token -> list of SymbolVariant
        
        # Common aliases to map mathematical tokens to folder/file names safely
        self.aliases = {
            '+': 'plus',
            '-': 'minus',
            '=': 'equals',
            '/': 'slash',
            '(': 'lparen',
            ')': 'rparen',
            '*': 'times'
        }
        self._load_symbols()

    def _load_symbols(self):
        if not os.path.exists(self.symbols_dir):
            raise FileNotFoundError(f"Symbols directory '{self.symbols_dir}' not found.")
            
        for root, dirs, files in os.walk(self.symbols_dir):
            for file in files:
                if file.endswith('.svg'):
                    filepath = os.path.join(root, file)
                    
                    # Infer token from parent directory and filename
                    parent = os.path.basename(root)
                    filename_token = file.split('_')[0] if '_' in file else os.path.splitext(file)[0]
                    
                    tokens_to_register = {parent, filename_token}
                    
                    try:
                        variant = SymbolVariant(filepath)
                        for t in tokens_to_register:
                            if t not in self.symbols:
                                self.symbols[t] = []
                            self.symbols[t].append(variant)
                    except Exception as e:
                        print(f"Warning: Failed to load {filepath}: {e}")

    def get_variants(self, token: str):
        # 1. Try direct match
        if token in self.symbols:
            return self.symbols[token]
        
        # 2. Try alias match
        alias = self.aliases.get(token)
        if alias and alias in self.symbols:
            return self.symbols[alias]
            
        raise ValueError(f"No symbol variants found for token: '{token}'")
