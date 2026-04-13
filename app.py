import streamlit as st
import os
import json
import base64
from backend import render_expression

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Handwritten Math Renderer",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# SESSION STATE INITIALIZATION
# ==========================================
if "expr_input" not in st.session_state:
    st.session_state.expr_input = ""
if "render_result" not in st.session_state:
    st.session_state.render_result = None

def load_example(mode):
    """Loads a sample expression based on the selected mode."""
    if mode == "LaTeX":
        st.session_state.expr_input = r"\int_0^1 x^2 \, dx"
    else:
        st.session_state.expr_input = '["x", "^2", "+", "2", "x", "+", "1", "=", "0"]'
    st.session_state.render_result = None

def clear_input():
    """Clears the input and preview."""
    st.session_state.expr_input = ""
    st.session_state.render_result = None

# ==========================================
# MAIN HEADER
# ==========================================
st.title("✍️ Handwritten Math Renderer")
st.markdown("Convert mathematical expressions into realistic handwritten-style outputs.")
st.divider()

# ==========================================
# THREE-PANEL LAYOUT
# ==========================================
col_left, col_center, col_right = st.columns([1.2, 2.0, 1.0], gap="large")

# ------------------------------------------
# LEFT PANEL: INPUT
# ------------------------------------------
with col_left:
    st.subheader("1. Input")
    
    input_mode = st.radio("Input Mode", ["LaTeX", "Tokens"], horizontal=True)
    
    # Action Buttons (Load Example / Clear)
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        st.button("Load Example", on_click=load_example, args=(input_mode,), use_container_width=True)
    with btn_col2:
        st.button("Clear", on_click=clear_input, use_container_width=True)
        
    # Main Expression Input
    expression = st.text_area(
        "Expression", 
        value=st.session_state.expr_input, 
        height=150, 
        key="expr_input",
        placeholder="\\int_0^1 x^2 \\, dx" if input_mode == "LaTeX" else '["x", "^2", "+", "1"]'
    )
    
    # Optional Settings
    with st.expander("⚙️ Rendering Settings"):
        variation_level = st.select_slider("Symbol Variation Level", options=["Low", "Medium", "High"], value="Medium")
        seed_input = st.text_input("Random Seed (optional)", placeholder="e.g., 42")
        output_format = st.selectbox("Output Format", ["SVG", "PNG", "PDF"])
        
    # Primary Render Button
    if st.button("🎨 Render", type="primary", use_container_width=True):
        seed_val = int(seed_input) if seed_input.strip().isdigit() else None
        with st.spinner("Rendering handwritten math..."):
            result = render_expression(
                expression=expression,
                input_mode=input_mode,
                variation_level=variation_level,
                seed=seed_val,
                output_format=output_format
            )
            st.session_state.render_result = result

# ------------------------------------------
# CENTER PANEL: PREVIEW
# ------------------------------------------
with col_center:
    st.subheader("2. Preview")
    
    res = st.session_state.render_result
    
    if res is None:
        # Friendly Placeholder
        st.info("👈 Enter an expression and click **Render** to see the handwritten preview.")
        st.markdown("""
            <div style="height: 300px; border: 2px dashed #ccc; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #888;">
                Preview Canvas
            </div>
        """, unsafe_allow_html=True)
        
    elif res.get("status") == "error":
        notes = res.get("notes", ["Unknown error"])
        st.error(f"**Error:** {notes[0]}")
        
    else:
        notes = res.get("notes", [])
        if notes:
            st.success(notes[0])
            for note in notes[1:]:
                st.warning(note)
                
        preview_path = res.get("output_files", {}).get("svg")
        
        if preview_path and os.path.exists(preview_path):
            with open(preview_path, "r", encoding="utf-8") as f:
                svg_content = f.read()
            
            b64_svg = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
            html_code = f"""
                <div style="overflow: auto; border: 1px solid #ddd; border-radius: 8px; padding: 20px; background: white; text-align: center; resize: both;">
                    <img src="data:image/svg+xml;base64,{b64_svg}" style="max-width: 100%; height: auto;" alt="Rendered Math"/>
                </div>
                <p style="font-size: 0.8em; color: gray; text-align: right;">Use browser zoom to scale.</p>
            """
            st.components.v1.html(html_code, height=350)
        else:
            st.warning("Preview file not found on disk.")

# ------------------------------------------
# RIGHT PANEL: STATUS & DETAILS
# ------------------------------------------
with col_right:
    st.subheader("3. Status & Details")
    
    res = st.session_state.render_result
    
    if res is None:
        st.markdown("**Status:** ⚪ Idle")
    elif res.get("status") == "error":
        st.markdown("**Status:** 🔴 Error")
    else:
        st.markdown("**Status:** 🟢 Done")
        
        st.markdown("#### Render Details")
        st.metric("Symbols Used", res.get("render_plan", {}).get("symbols_used", 0))
        
        structures = res.get("document_structure", {}).get("detected", [])
        if structures:
            st.markdown("**Detected Structures:**")
            for struct in structures:
                st.markdown(f"- `{struct.capitalize()}`")
                
        st.divider()
        st.markdown("#### Output Actions")
        
        # Determine the correct output path based on format and fallback
        output_files = res.get("output_files", {})
        output_path = ""
        dl_format = output_format
        
        if output_format == "SVG" and output_files.get("svg"):
            output_path = output_files["svg"]
        elif output_format == "PNG" and output_files.get("png"):
            output_path = output_files["png"]
        elif output_format == "PDF" and output_files.get("pdf"):
            output_path = output_files["pdf"]
        else:
            # Fallback to SVG if the requested format failed
            output_path = output_files.get("svg", "")
            dl_format = "SVG"
        
        if output_path and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                file_bytes = f.read()
                
            mime_type = "image/svg+xml" if dl_format == "SVG" else "application/octet-stream"
            
            st.download_button(
                label=f"⬇️ Download {dl_format}",
                data=file_bytes,
                file_name=os.path.basename(output_path),
                mime=mime_type,
                use_container_width=True
            )
            
            st.text_input("Output Path (Copy)", value=os.path.abspath(output_path), disabled=True)
            st.caption("*(Opening local folders directly from the browser is restricted for security. Copy the path above to access the file.)*")

st.divider()

# ==========================================
# BOTTOM PANELS: INFO & LIMITATIONS
# ==========================================
col_info1, col_info2 = st.columns(2, gap="large")

with col_info1:
    st.markdown("### ✅ Supported Symbols and Structures")
    st.markdown("""
    The current version supports the following mathematical constructs:
    - **Basic characters**: Letters `a-z`, `A-Z`, and numbers `0-9`
    - **Operators**: `+`, `-`, `=`, `(`, `)`
    - **Structures**: 
      - Powers `^` and Subscripts `_`
      - Fractions `\frac{a}{b}`
      - Square roots `\sqrt{x}`
    - **Calculus**: 
      - Integrals `\int_a^b`
      - Summations `\sum_{n=1}^\infty`
      - Limits `\lim_{x \to 0}`
      - Partial derivatives `\partial`, Gradient `\nabla`
      
    **Layout Behavior:**
    Includes baseline alignment, exponent positioning, fraction stacking, and natural handwritten variation through symbol variants.
    """)

with col_info2:
    st.markdown("### ⚠️ Current Limitations")
    st.info("""
    **First-Version Constraints:**
    - Only the listed symbols and structures are supported.
    - Complex LaTeX packages (e.g., `amsmath`, `tikz`) are **not** supported.
    - Full LaTeX documents are not supported; provide clean mathematical expressions only.
    - Advanced environments such as `align`, `cases`, or `matrix` may not work.
    - Multi-page layout is not part of the first version.
    - PDF input is not supported (only LaTeX strings or Token lists).
    """)
