import xml.etree.ElementTree as ET
import copy
from .config import RenderConfig
from .loader import SymbolLoader
from .selector import VariantSelector

class Renderer:
    def __init__(self, loader: SymbolLoader, selector: VariantSelector, config: RenderConfig):
        self.loader = loader
        self.selector = selector
        self.config = config

    def render(self, tokens: list, output_path: str):
        items = self._layout(tokens)
        
        if not items:
            raise ValueError("No items to render. Token list might be empty.")
            
        # Compute the bounding box of the entire expression
        min_x = min(item['x'] for item in items)
        min_y = min(item['y'] for item in items)
        max_x = max(item['x'] + item['width'] for item in items)
        max_y = max(item['y'] + item['height'] for item in items)
        
        pad = self.config.padding
        width = max_x - min_x + 2 * pad
        height = max_y - min_y + 2 * pad
        
        # Create SVG root
        svg = ET.Element('svg', {
            'xmlns': 'http://www.w3.org/2000/svg',
            'width': f"{width:.2f}",
            'height': f"{height:.2f}",
            'viewBox': f"0 0 {width:.2f} {height:.2f}"
        })
        
        # Main group with translation to account for padding and negative coordinates
        g_main = ET.SubElement(svg, 'g', {
            'transform': f"translate({pad - min_x:.2f}, {pad - min_y:.2f})"
        })
        
        for item in items:
            variant = item['variant']
            
            # SVG transforms are applied right-to-left.
            # We translate to the target (x, y), rotate around the center of the scaled symbol, and scale.
            transform = f"translate({item['x']:.2f}, {item['y']:.2f}) "
            transform += f"rotate({item['rot']:.2f}, {item['width']/2:.2f}, {item['height']/2:.2f}) "
            transform += f"scale({item['scale']:.2f})"
            
            g_sym = ET.SubElement(g_main, 'g', {'transform': transform})
            
            # Deepcopy elements so we don't mutate the cached variants
            for elem in variant.elements:
                g_sym.append(copy.deepcopy(elem))
                
        # Write to file
        tree = ET.ElementTree(svg)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        if self.config.export_png:
            self._export_png(output_path)

    def _layout(self, tokens: list):
        items = []
        cursor_x = 0
        baseline_y = 100 # Arbitrary starting baseline
        
        for token in tokens:
            if token.startswith('^'):
                # Handle exponents (supports multi-character like "^2x")
                exp_tokens = list(token[1:])
                
                for i, exp_token in enumerate(exp_tokens):
                    variants = self.loader.get_variants(exp_token)
                    variant = self.selector.select(exp_token, variants)
                    
                    scale = self.config.default_scale * self.config.exponent_scale
                    scale *= (1.0 + self.selector.rng.uniform(-self.config.scale_jitter_pct, self.config.scale_jitter_pct))
                    rot = self.selector.rng.uniform(-self.config.rot_jitter_deg, self.config.rot_jitter_deg)
                    
                    width = variant.width * scale
                    height = variant.height * scale
                    
                    if i == 0:
                        if items:
                            prev = items[-1]
                            x = prev['x'] + prev['width'] + self.config.exponent_x_offset
                            # Place exponent so its bottom is near the top of the base symbol
                            y = prev['y'] - height * 0.5 + self.config.exponent_y_offset
                        else:
                            x = cursor_x
                            y = baseline_y - height
                    else:
                        # Subsequent characters in the exponent
                        prev = items[-1]
                        x = prev['x'] + prev['width'] + self.config.base_spacing * 0.5
                        y = prev['y']
                        
                    cursor_x = x + width + self.config.base_spacing * 0.5
                    
                    items.append({
                        'variant': variant, 'x': x, 'y': y,
                        'scale': scale, 'rot': rot, 'width': width, 'height': height
                    })
            else:
                # Normal symbols
                variants = self.loader.get_variants(token)
                variant = self.selector.select(token, variants)
                
                scale = self.config.default_scale
                scale *= (1.0 + self.selector.rng.uniform(-self.config.scale_jitter_pct, self.config.scale_jitter_pct))
                rot = self.selector.rng.uniform(-self.config.rot_jitter_deg, self.config.rot_jitter_deg)
                
                x_jitter = self.selector.rng.uniform(-self.config.x_jitter_px, self.config.x_jitter_px)
                y_jitter = self.selector.rng.uniform(-self.config.y_jitter_px, self.config.y_jitter_px)
                spacing_jitter = self.selector.rng.uniform(-self.config.spacing_jitter_px, self.config.spacing_jitter_px)
                
                width = variant.width * scale
                height = variant.height * scale
                
                x = cursor_x + x_jitter
                # Align vertical center to baseline. This is a robust heuristic for mixed symbols.
                y = baseline_y - (height / 2) + y_jitter
                
                cursor_x = x + width + self.config.base_spacing + spacing_jitter
                
                items.append({
                    'variant': variant, 'x': x, 'y': y,
                    'scale': scale, 'rot': rot, 'width': width, 'height': height
                })
                
        return items

    def _export_png(self, svg_path: str):
        png_path = svg_path.rsplit('.', 1)[0] + '.png'
        try:
            import cairosvg
            cairosvg.svg2png(url=svg_path, write_to=png_path)
            print(f"Exported PNG to {png_path}")
        except ImportError:
            print("Warning: cairosvg not installed. Skipping PNG export. Install with: pip install cairosvg")
