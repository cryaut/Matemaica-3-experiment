import React, { useState } from 'react';
import { Play, Trash2, FileText, Download, Settings, AlertCircle, CheckCircle2, Info, Code, Edit3 } from 'lucide-react';
import { jsPDF } from 'jspdf';
import 'svg2pdf.js';
import { renderExpression, RenderResult } from './lib/backend';

export default function App() {
  const [mode, setMode] = useState<'LaTeX' | 'Tokens'>('LaTeX');
  const [expression, setExpression] = useState('');
  const [variation, setVariation] = useState('Medium');
  const [seed, setSeed] = useState('');
  const [format, setFormat] = useState('SVG');
  const [pageStyle, setPageStyle] = useState('Blank');
  const [inkColor, setInkColor] = useState('#333333');
  const [showSettings, setShowSettings] = useState(false);
  
  const [isRendering, setIsRendering] = useState(false);
  const [result, setResult] = useState<RenderResult | null>(null);

  const handleLoadExample = () => {
    if (mode === 'LaTeX') {
      setExpression('\\int_0^1 x^2 \\, dx');
    } else {
      setExpression('["x", "^2", "+", "2", "x", "+", "1", "=", "0"]');
    }
    setResult(null);
  };

  const handleClear = () => {
    setExpression('');
    setResult(null);
  };

  const handleRender = async () => {
    setIsRendering(true);
    const res = await renderExpression(expression, mode, variation, seed ? parseInt(seed) : null, format, pageStyle, inkColor);
    setResult(res);
    setIsRendering(false);
  };

  const triggerDownload = (url: string, filename: string) => {
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleDownload = async () => {
    if (!result?.svgPages || result.svgPages.length === 0) return;

    if (format === 'SVG') {
      // For SVG, we can just download the first page or combine them.
      // For simplicity, download the first page if there's only one, or zip them (but we don't have JSZip).
      // Let's just download the first page for SVG.
      const blob = new Blob([result.svgPages[0]], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      triggerDownload(url, `handwritten_math_${Date.now()}.svg`);
      URL.revokeObjectURL(url);
    } else if (format === 'PDF') {
      // Create a multi-page PDF using svg2pdf
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'pt',
        format: [800, 1130] // Our PAGE_WIDTH and PAGE_HEIGHT
      });

      // Load and register the custom font
      try {
        const fontResponse = await fetch('/WaHandwriting-Regular.ttf');
        const fontBlob = await fontResponse.blob();
        const reader = new FileReader();
        const fontBase64 = await new Promise<string>((resolve) => {
          reader.onloadend = () => {
            const result = reader.result as string;
            resolve(result.split(',')[1]);
          };
          reader.readAsDataURL(fontBlob);
        });
        
        pdf.addFileToVFS('WaHandwriting-Regular.ttf', fontBase64);
        pdf.addFont('WaHandwriting-Regular.ttf', 'WaHandwriting-Regular', 'normal');
        pdf.addFont('WaHandwriting-Regular.ttf', 'WaHandwriting-Regular', 'bold');
        pdf.addFont('WaHandwriting-Regular.ttf', 'WaHandwriting-Regular', 'italic');
        pdf.setFont('WaHandwriting-Regular');
      } catch (e) {
        console.error("Failed to load custom font for PDF:", e);
      }

      for (let i = 0; i < result.svgPages.length; i++) {
        if (i > 0) {
          pdf.addPage([800, 1130], 'portrait');
        }
        
        // Create a temporary DOM element to parse the SVG
        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(result.svgPages[i], 'image/svg+xml');
        const svgElement = svgDoc.documentElement;
        
        // We need to append it to the body temporarily for svg2pdf to work correctly with fonts
        svgElement.style.position = 'absolute';
        svgElement.style.left = '-9999px';
        document.body.appendChild(svgElement);
        
        await pdf.svg(svgElement, {
          x: 0,
          y: 0,
          width: 800,
          height: 1130
        });
        
        document.body.removeChild(svgElement);
      }
      
      pdf.save(`handwritten_math_${Date.now()}.pdf`);
    } else if (format === 'PNG') {
      // For PNG, just render the first page
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();
      const svgBlob = new Blob([result.svgPages[0]], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);

      img.onload = () => {
        const width = img.width || 800;
        const height = img.height || 1130;
        
        canvas.width = width;
        canvas.height = height;
        
        if (ctx) {
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        }

        const pngDataUrl = canvas.toDataURL('image/png');
        triggerDownload(pngDataUrl, `handwritten_math_${Date.now()}.png`);
        URL.revokeObjectURL(url);
      };
      img.src = url;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8 text-gray-900 font-sans">
      <header className="mb-8 max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Edit3 className="text-blue-600 w-8 h-8" /> Handwritten Math Renderer
        </h1>
        <p className="text-gray-600 mt-2 text-lg">Convert mathematical expressions into realistic handwritten-style outputs.</p>
      </header>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT PANEL: INPUT */}
        <div className="lg:col-span-3 space-y-6 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-xl font-semibold flex items-center gap-2 border-b pb-2">
            <Code className="w-5 h-5 text-gray-500" /> 1. Input
          </h2>
          
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">Input Mode</label>
            <div className="flex bg-gray-100 p-1 rounded-lg">
              <button 
                onClick={() => setMode('LaTeX')}
                className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${mode === 'LaTeX' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
              >
                LaTeX
              </button>
              <button 
                onClick={() => setMode('Tokens')}
                className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${mode === 'Tokens' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
              >
                Tokens
              </button>
            </div>
          </div>

          <div className="flex gap-2">
            <button onClick={handleLoadExample} className="flex-1 flex items-center justify-center gap-1 py-2 px-3 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-lg transition-colors">
              <FileText className="w-4 h-4" /> Example
            </button>
            <button onClick={handleClear} className="flex-1 flex items-center justify-center gap-1 py-2 px-3 bg-gray-100 hover:bg-red-50 text-gray-700 hover:text-red-600 text-sm font-medium rounded-lg transition-colors">
              <Trash2 className="w-4 h-4" /> Clear
            </button>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Expression</label>
            <textarea 
              value={expression}
              onChange={(e) => setExpression(e.target.value)}
              placeholder={mode === 'LaTeX' ? '\\int_0^1 x^2 \\, dx' : '["x", "^2", "+", "1"]'}
              className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm resize-none"
            />
          </div>

          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <button 
              onClick={() => setShowSettings(!showSettings)}
              className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 text-sm font-medium text-gray-700 transition-colors"
            >
              <span className="flex items-center gap-2"><Settings className="w-4 h-4" /> Rendering Settings</span>
              <span>{showSettings ? '▲' : '▼'}</span>
            </button>
            {showSettings && (
              <div className="p-4 space-y-4 bg-white border-t border-gray-200">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Variation Level</label>
                  <select value={variation} onChange={(e) => setVariation(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md text-sm">
                    <option>Low</option>
                    <option>Medium</option>
                    <option>High</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Random Seed (optional)</label>
                  <input type="number" value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="e.g. 42" className="w-full p-2 border border-gray-300 rounded-md text-sm" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Output Format</label>
                  <select value={format} onChange={(e) => setFormat(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md text-sm">
                    <option>SVG</option>
                    <option>PNG</option>
                    <option>PDF</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Page Style</label>
                  <select value={pageStyle} onChange={(e) => setPageStyle(e.target.value)} className="w-full p-2 border border-gray-300 rounded-md text-sm">
                    <option>Blank</option>
                    <option>Lined</option>
                    <option>Grid</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Ink Color</label>
                  <div className="flex items-center gap-2">
                    <input 
                      type="color" 
                      value={inkColor} 
                      onChange={(e) => setInkColor(e.target.value)} 
                      className="w-8 h-8 rounded cursor-pointer border border-gray-300 p-0.5" 
                    />
                    <span className="text-sm text-gray-600 font-mono">{inkColor}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <button 
            onClick={handleRender}
            disabled={isRendering || !expression.trim()}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold rounded-lg shadow-sm transition-colors"
          >
            {isRendering ? (
              <span className="animate-pulse">Rendering...</span>
            ) : (
              <><Play className="w-5 h-5 fill-current" /> Render</>
            )}
          </button>
        </div>

        {/* CENTER PANEL: PREVIEW */}
        <div className="lg:col-span-6 space-y-6 bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex flex-col">
          <h2 className="text-xl font-semibold flex items-center gap-2 border-b pb-2">
            <FileText className="w-5 h-5 text-gray-500" /> 2. Preview
          </h2>
          
          <div className="flex-1 flex flex-col">
            {!result ? (
              <div className="flex-1 min-h-[300px] border-2 border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center text-gray-500 bg-gray-50">
                <Edit3 className="w-12 h-12 mb-3 text-gray-400" />
                <p>Enter an expression and click <strong>Render</strong></p>
                <p className="text-sm">to see the handwritten preview.</p>
              </div>
            ) : result.status === 'error' ? (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3 text-red-700">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold">Render Error</h3>
                  <p className="text-sm mt-1">{result.message}</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col h-full space-y-4">
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-700 text-sm font-medium">
                  <CheckCircle2 className="w-5 h-5" /> {result.message}
                </div>
                
                <div className="flex-1 border border-gray-200 rounded-xl overflow-hidden bg-gray-100 shadow-inner relative min-h-[300px] flex flex-col items-center p-4 gap-4 overflow-y-auto">
                  {result.svgPages && result.svgPages.length > 0 ? (
                    result.svgPages.map((pageSvg, idx) => (
                      <div 
                        key={idx}
                        className="w-full max-w-[800px] bg-white shadow-md rounded-sm flex-shrink-0 [&>svg]:w-full [&>svg]:h-auto"
                        dangerouslySetInnerHTML={{ __html: pageSvg }}
                      />
                    ))
                  ) : (
                    <div className="text-center text-gray-500 m-auto">
                      <p className="font-medium">Preview not available</p>
                    </div>
                  )}
                </div>
                <p className="text-xs text-gray-400 text-right">Use browser zoom to scale.</p>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL: STATUS */}
        <div className="lg:col-span-3 space-y-6 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h2 className="text-xl font-semibold flex items-center gap-2 border-b pb-2">
            <Info className="w-5 h-5 text-gray-500" /> 3. Status & Details
          </h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Render Status</h3>
              <div className="flex items-center gap-2 font-medium">
                {!result && !isRendering && <><span className="w-3 h-3 rounded-full bg-gray-300"></span> Idle</>}
                {isRendering && <><span className="w-3 h-3 rounded-full bg-blue-500 animate-pulse"></span> Rendering</>}
                {result?.status === 'done' && <><span className="w-3 h-3 rounded-full bg-green-500"></span> Done</>}
                {result?.status === 'error' && <><span className="w-3 h-3 rounded-full bg-red-500"></span> Error</>}
              </div>
            </div>

            {result?.status === 'done' && (
              <>
                <div className="pt-4 border-t border-gray-100">
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">Render Details</h3>
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
                    <div className="text-3xl font-bold text-gray-900">{result.symbolsUsed}</div>
                    <div className="text-sm text-gray-500 font-medium">Symbols Used</div>
                  </div>
                  
                  {result.detectedStructures && result.detectedStructures.length > 0 && (
                    <div className="mt-4">
                      <div className="text-sm text-gray-700 font-medium mb-2">Detected Structures:</div>
                      <div className="flex flex-wrap gap-2">
                        {result.detectedStructures.map((struct, idx) => (
                          <span key={idx} className="px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-md border border-blue-100">
                            {struct}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t border-gray-100">
                  <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-3">Output Actions</h3>
                  <button 
                    onClick={handleDownload}
                    className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
                  >
                    <Download className="w-4 h-4" /> Download {format}
                  </button>
                  <p className="text-xs text-gray-500 mt-3 text-center">
                    File will be saved directly to your local downloads folder.
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* BOTTOM PANELS */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4 text-green-700">
            <CheckCircle2 className="w-5 h-5" /> Supported Symbols and Structures
          </h3>
          <div className="text-sm text-gray-600 space-y-2">
            <p>The current version supports the following mathematical constructs:</p>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li><strong>Basic characters</strong>: Letters <code>a-z</code>, <code>A-Z</code>, and numbers <code>0-9</code></li>
              <li><strong>Operators</strong>: <code>+</code>, <code>-</code>, <code>=</code>, <code>(</code>, <code>)</code>, <code>\times</code>, <code>\cdot</code>, <code>\approx</code>, <code>\sim</code>, <code>\propto</code></li>
              <li><strong>Structures</strong>: Powers <code>^</code>, Subscripts <code>_</code>, Fractions <code>\frac{"{a}{b}"}</code>, Square roots <code>\sqrt{"{x}"}</code>, Binomials <code>\binom{"{n}{k}"}</code>, Accents <code>\vec</code>, <code>\hat</code>, <code>\dot</code>, <code>\ddot</code></li>
              <li><strong>Calculus</strong>: Integrals <code>\int</code>, <code>\iint</code>, <code>\iiint</code>, <code>\oint</code>, <code>\oiint</code>, Summations <code>\sum</code>, Products <code>\prod</code>, <code>\coprod</code>, Limits <code>\lim</code>, Partial derivatives <code>\partial</code>, Gradient <code>\nabla</code>, Laplacian <code>\Delta</code></li>
              <li><strong>Sets & Logic</strong>: Union <code>\bigcup</code>, Intersection <code>\bigcap</code>, Infinity <code>\infty</code>, Arrow <code>\to</code>, <code>\Rightarrow</code>, <code>\Leftarrow</code>, <code>\Leftrightarrow</code>, <code>\rightarrow</code>, <code>\leftarrow</code>, <code>\leftrightarrow</code></li>
              <li><strong>Relations</strong>: <code>\ge</code>, <code>\le</code>, <code>\geq</code>, <code>\leq</code></li>
              <li><strong>Spacing</strong>: <code>\,</code>, <code>\;</code>, <code>\quad</code>, <code>\qquad</code></li>
            </ul>
            <p className="mt-4 font-medium text-gray-800">Layout Behavior:</p>
            <p>Includes baseline alignment, exponent positioning, fraction stacking, and natural handwritten variation through symbol variants.</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4 text-amber-600">
            <AlertCircle className="w-5 h-5" /> Current Limitations
          </h3>
          <div className="text-sm text-gray-600 space-y-2">
            <p className="font-medium text-gray-800">First-Version Constraints:</p>
            <ul className="list-disc pl-5 space-y-1 mt-2">
              <li>Only the listed symbols and structures are supported.</li>
              <li>Complex LaTeX packages (e.g., <code>amsmath</code>, <code>tikz</code>) are <strong>not</strong> supported.</li>
              <li>Full LaTeX documents are not supported; provide clean mathematical expressions only.</li>
              <li>Advanced environments such as <code>align</code>, <code>cases</code>, or <code>matrix</code> may not work.</li>
              <li>Multi-page layout is not part of the first version.</li>
              <li>PDF input is not supported (only LaTeX strings or Token lists).</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
