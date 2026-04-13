# Handwritten Math Renderer UI

A simple, clean, and fast user interface for the Handwritten Math Rendering system, built with [Streamlit](https://streamlit.io/).

## Layout Overview

The interface is designed with usability in mind, utilizing a clean three-panel layout:
1. **Left Panel (Input)**: Contains the input mode selector (LaTeX/Tokens), the main expression text area, action buttons (Load Example, Clear, Render), and an expandable settings section for variation level, seed, and output format.
2. **Center Panel (Preview)**: Displays the generated handwritten output. It uses a clean placeholder when idle and renders the generated SVG directly in the browser with a scrollable container.
3. **Right Panel (Status & Details)**: Shows the current render status, metrics (symbols used, detected structures), and provides a one-click download button for the generated file.

At the bottom, two clear sections outline the **Supported Symbols and Structures** and the **Current Limitations**, ensuring the user understands the system's capabilities.

## Backend Connection

The UI connects to the backend via a simple contract defined in `backend.py`. 
The `render_expression()` function takes the user inputs (`expression`, `input_mode`, `variation_level`, `seed`, `output_format`) and returns a dictionary containing the status, file paths, and metadata. 

The frontend uses Streamlit's `st.session_state` to store this result and dynamically update the Preview and Status panels without losing the user's input.

## How to Run Locally

1. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
3. Open the provided local URL in your browser (usually `http://localhost:8501`).

## Example Interaction

1. Select **LaTeX** as the Input Mode.
2. Click **Load Example** to automatically insert `\int_0^1 x^2 \, dx`.
3. Click **Render**.
4. The backend stub will simulate processing, detect the `integral` and `power` structures, and generate a dummy SVG.
5. The Center Panel will display the simulated handwritten SVG.
6. The Right Panel will update to show "Done", list the detected structures, and provide a button to download the SVG.
