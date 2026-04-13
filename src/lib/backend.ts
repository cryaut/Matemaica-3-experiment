export interface RenderResult {
  status: 'done' | 'error';
  message: string;
  svgContent?: string;
  symbolsUsed?: number;
  detectedStructures?: string[];
}

export async function renderExpression(
  expression: string,
  mode: string,
  variation: string,
  seed: number | null,
  format: string
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
        output_format: format
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.status === 'error') {
      return {
        status: 'error',
        message: data.notes ? data.notes[0] : 'Unknown error occurred in Python backend.'
      };
    }

    return {
      status: 'done',
      message: data.notes ? data.notes[0] : 'Rendered successfully',
      svgContent: data.svg_content,
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
