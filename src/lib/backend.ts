export interface RenderResult {
  status: 'done' | 'error';
  message: string;
  svgPages?: string[];
  symbolsUsed?: number;
  detectedStructures?: string[];
}

export interface CustomSymbolPayload {
  latex: string;
  svg: string;
  width: number;
  height: number;
  baseline: number;
}

export async function renderExpression(
  expression: string,
  mode: string,
  variation: string,
  seed: number | null,
  format: string,
  pageStyle: string = 'Blank',
  inkColor: string = '#333333',
  customSymbols: CustomSymbolPayload[] = []
): Promise<RenderResult> {
  try {
    const response = await fetch('/api/render', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        expression,
        input_mode: mode,
        variation_level: variation,
        seed,
        output_format: format,
        page_style: pageStyle,
        ink_color: inkColor,
        custom_symbols: customSymbols
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const text = await response.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      console.error("Failed to parse backend response as JSON. Raw response:", text);
      throw new Error(`Invalid JSON response from server: ${text.substring(0, 100)}...`);
    }

    if (data.status === 'error') {
      return {
        status: 'error',
        message: data.notes ? data.notes[0] : 'Unknown error occurred in Python backend.'
      };
    }

    return {
      status: 'done',
      message: data.notes ? data.notes[0] : 'Rendered successfully',
      svgPages: data.svg_pages,
      symbolsUsed: data.render_plan?.symbols_used || 0,
      detectedStructures: data.document_structure?.detected || []
    };
  } catch (error: any) {
    console.error("Backend fetch error:", error);
    return {
      status: 'error',
      message: `Failed to connect to Python backend: ${error.message}`
    };
  }
}
