from .config import RenderConfig
from .loader import SymbolLoader
from .selector import VariantSelector
from .renderer import Renderer

def render_expression(tokens: list, symbols_dir: str = "symbols", output_path: str = "output.svg", seed: int = None, export_png: bool = False):
    """
    Main entry point to render a mathematical expression into a handwritten SVG.
    
    :param tokens: List of string tokens, e.g., ["x", "^2", "+", "1"]
    :param symbols_dir: Path to the directory containing SVG symbol variants
    :param output_path: Where to save the final SVG
    :param seed: Optional random seed for reproducible variation
    :param export_png: Whether to also export a PNG (requires cairosvg)
    """
    config = RenderConfig()
    config.export_png = export_png
    
    loader = SymbolLoader(symbols_dir)
    selector = VariantSelector(seed)
    renderer = Renderer(loader, selector, config)
    
    renderer.render(tokens, output_path)
