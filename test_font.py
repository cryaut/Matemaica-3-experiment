import base64
import os

font_path = os.path.join("public", "WaHandwriting-Regular.ttf")
if os.path.exists(font_path):
    with open(font_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    print(f"Font size: {len(encoded)}")
else:
    print("Font not found")
