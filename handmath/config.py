from dataclasses import dataclass

@dataclass
class RenderConfig:
    # Scaling and spacing
    default_scale: float = 1.0
    base_spacing: float = 10.0
    
    # Randomness (Jitter)
    rot_jitter_deg: float = 3.0
    scale_jitter_pct: float = 0.05
    y_jitter_px: float = 2.0
    x_jitter_px: float = 1.0
    spacing_jitter_px: float = 2.0
    
    # Exponents
    exponent_scale: float = 0.65
    exponent_x_offset: float = 2.0
    exponent_y_offset: float = -5.0  # Relative to base
    
    # Output
    padding: float = 20.0
    export_png: bool = False
