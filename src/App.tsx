import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Code,
  Download,
  Eraser,
  FileText,
  PenLine,
  Play,
  Redo2,
  Save,
  Settings,
  Trash2,
  Undo2,
} from 'lucide-react';
import { jsPDF } from 'jspdf';
import 'svg2pdf.js';
import { renderExpression, RenderResult, CustomSymbolPayload } from './lib/backend';
import { symbolCatalog, symbolCategories, SymbolCatalogItem } from './symbolCatalog';

type Point = { x: number; y: number };
type Stroke = { points: Point[]; color: string; size: number };
type SavedSymbol = CustomSymbolPayload & {
  label: string;
  category: string;
  strokes: Stroke[];
  savedAt: number;
};

const STORAGE_KEY = 'handmath.customSymbols.v1';
const CANVAS_WIDTH = 320;
const CANVAS_HEIGHT = 200;
const SYMBOL_TARGET_HEIGHT = 28;
const SYMBOL_BASELINE = 22;
const SYMBOL_MIN_ADVANCE = 6;
const SYMBOL_MAX_ADVANCE = 38;
const SYMBOL_CROP_PADDING = 4;

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function hasVisibleInk(strokes: Stroke[]) {
  return strokes.some((stroke) => stroke.color !== '#ffffff' && stroke.points.length > 1);
}

function buildSymbolAsset(strokes: Stroke[]): Omit<CustomSymbolPayload, 'latex'> {
  const inkStrokes = strokes.filter((stroke) => stroke.color !== '#ffffff' && stroke.points.length > 1);
  const allInkPoints = inkStrokes.flatMap((stroke) => stroke.points);

  if (!allInkPoints.length) {
    return {
      svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1" width="${SYMBOL_MIN_ADVANCE}" height="${SYMBOL_TARGET_HEIGHT}"></svg>`,
      width: SYMBOL_MIN_ADVANCE,
      height: SYMBOL_TARGET_HEIGHT,
      baseline: SYMBOL_BASELINE,
    };
  }

  const maxStrokeRadius = Math.max(...inkStrokes.map((stroke) => stroke.size / 2));
  const minX = Math.max(0, Math.min(...allInkPoints.map((point) => point.x)) - maxStrokeRadius - SYMBOL_CROP_PADDING);
  const minY = Math.max(0, Math.min(...allInkPoints.map((point) => point.y)) - maxStrokeRadius - SYMBOL_CROP_PADDING);
  const maxX = Math.min(CANVAS_WIDTH, Math.max(...allInkPoints.map((point) => point.x)) + maxStrokeRadius + SYMBOL_CROP_PADDING);
  const maxY = Math.min(CANVAS_HEIGHT, Math.max(...allInkPoints.map((point) => point.y)) + maxStrokeRadius + SYMBOL_CROP_PADDING);

  const cropWidth = Math.max(1, maxX - minX);
  const cropHeight = Math.max(1, maxY - minY);
  const metricWidth = clamp((cropWidth / cropHeight) * SYMBOL_TARGET_HEIGHT, SYMBOL_MIN_ADVANCE, SYMBOL_MAX_ADVANCE);

  const paths = strokes
    .filter((stroke) => stroke.points.length > 1)
    .map((stroke) => {
      const [first, ...rest] = stroke.points;
      const d = [`M ${(first.x - minX).toFixed(1)} ${(first.y - minY).toFixed(1)}`]
        .concat(rest.map((point) => `L ${(point.x - minX).toFixed(1)} ${(point.y - minY).toFixed(1)}`))
        .join(' ');
      return `<path d="${d}" stroke="${stroke.color}" stroke-width="${stroke.size}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`;
    })
    .join('');

  return {
    svg: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${cropWidth.toFixed(1)} ${cropHeight.toFixed(1)}" width="${metricWidth.toFixed(2)}" height="${SYMBOL_TARGET_HEIGHT}">${paths}</svg>`,
    width: Number(metricWidth.toFixed(2)),
    height: SYMBOL_TARGET_HEIGHT,
    baseline: SYMBOL_BASELINE,
  };
}

function loadSavedSymbols(): SavedSymbol[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];

    const saved = JSON.parse(raw) as SavedSymbol[];
    return saved.map((item) => {
      if (!item.strokes?.length) return item;
      return { ...item, ...buildSymbolAsset(item.strokes) };
    });
  } catch {
    return [];
  }
}

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

  const [activeCategory, setActiveCategory] = useState(symbolCategories[0]);
  const [selectedSymbol, setSelectedSymbol] = useState<SymbolCatalogItem>(symbolCatalog[0]);
  const [savedSymbols, setSavedSymbols] = useState<SavedSymbol[]>(() => loadSavedSymbols());
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [redoStack, setRedoStack] = useState<Stroke[]>([]);
  const [tool, setTool] = useState<'pen' | 'eraser'>('pen');
  const [strokeSize, setStrokeSize] = useState(4);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const drawingRef = useRef(false);

  const customSymbolPayload = useMemo(
    () => savedSymbols.map(({ latex, svg, width, height, baseline }) => ({ latex, svg, width, height, baseline })),
    [savedSymbols]
  );
  const currentSymbolAsset = useMemo(() => buildSymbolAsset(strokes), [strokes]);
  const canSaveSymbol = hasVisibleInk(strokes);

  const filteredSymbols = useMemo(
    () => symbolCatalog.filter((item) => item.category === activeCategory),
    [activeCategory]
  );

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(savedSymbols));
  }, [savedSymbols]);

  useEffect(() => {
    const saved = savedSymbols.find((item) => item.latex === selectedSymbol.latex);
    setStrokes(saved?.strokes ?? []);
    setRedoStack([]);
  }, [selectedSymbol, savedSymbols]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let x = 32; x < CANVAS_WIDTH; x += 32) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, CANVAS_HEIGHT);
      ctx.stroke();
    }
    for (let y = 32; y < CANVAS_HEIGHT; y += 32) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(CANVAS_WIDTH, y);
      ctx.stroke();
    }

    strokes.forEach((stroke) => {
      if (stroke.points.length < 2) return;
      ctx.strokeStyle = stroke.color;
      ctx.lineWidth = stroke.size;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();
      ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
      stroke.points.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
      ctx.stroke();
    });
  }, [strokes]);

  const pointerToPoint = (event: React.PointerEvent<HTMLCanvasElement>): Point => {
    const rect = event.currentTarget.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * CANVAS_WIDTH,
      y: ((event.clientY - rect.top) / rect.height) * CANVAS_HEIGHT,
    };
  };

  const beginStroke = (event: React.PointerEvent<HTMLCanvasElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId);
    drawingRef.current = true;
    setRedoStack([]);
    const point = pointerToPoint(event);
    setStrokes((current) => [...current, { points: [point], color: tool === 'pen' ? '#111827' : '#ffffff', size: tool === 'pen' ? strokeSize : strokeSize * 3 }]);
  };

  const continueStroke = (event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawingRef.current) return;
    const point = pointerToPoint(event);
    setStrokes((current) => {
      const next = [...current];
      const last = next[next.length - 1];
      next[next.length - 1] = { ...last, points: [...last.points, point] };
      return next;
    });
  };

  const endStroke = () => {
    drawingRef.current = false;
  };

  const handleLoadExample = () => {
    if (mode === 'LaTeX') {
      setExpression('\\begin{align*}\\n\\int_0^1 x^2\\,dx &= \\frac{1}{3} \\\\\\nA &= \\begin{pmatrix} a & b \\\\\\ c & d \\end{pmatrix}\\n\\end{align*}');
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
    const res = await renderExpression(expression, mode, variation, seed ? parseInt(seed) : null, format, pageStyle, inkColor, customSymbolPayload);
    setResult(res);
    setIsRendering(false);
  };

  const insertLatex = (latex: string) => {
    const textarea = document.getElementById('math-input') as HTMLTextAreaElement;
    if (!textarea) return;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const newText = expression.substring(0, start) + latex + expression.substring(end);
    setExpression(newText);
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + latex.length, start + latex.length);
    }, 0);
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
    if (!result?.svgPages?.length) return;

    if (format === 'SVG') {
      const blob = new Blob([result.svgPages[0]], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      triggerDownload(url, `handwritten_math_${Date.now()}.svg`);
      URL.revokeObjectURL(url);
      return;
    }

    if (format === 'PDF') {
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'pt', format: [800, 1130] });
      for (let i = 0; i < result.svgPages.length; i++) {
        if (i > 0) pdf.addPage([800, 1130], 'portrait');
        const svgElement = new DOMParser().parseFromString(result.svgPages[i], 'image/svg+xml').documentElement;
        svgElement.style.position = 'absolute';
        svgElement.style.left = '-9999px';
        document.body.appendChild(svgElement);
        await pdf.svg(svgElement, { x: 0, y: 0, width: 800, height: 1130 });
        document.body.removeChild(svgElement);
      }
      pdf.save(`handwritten_math_${Date.now()}.pdf`);
      return;
    }

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    const svgBlob = new Blob([result.svgPages[0]], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);
    img.onload = () => {
      canvas.width = img.width || 800;
      canvas.height = img.height || 1130;
      ctx?.fillRect(0, 0, canvas.width, canvas.height);
      ctx?.drawImage(img, 0, 0, canvas.width, canvas.height);
      triggerDownload(canvas.toDataURL('image/png'), `handwritten_math_${Date.now()}.png`);
      URL.revokeObjectURL(url);
    };
    img.src = url;
  };

  const undoStroke = () => {
    setStrokes((current) => {
      if (!current.length) return current;
      const removed = current[current.length - 1];
      setRedoStack((redo) => [removed, ...redo]);
      return current.slice(0, -1);
    });
  };

  const redoStroke = () => {
    setRedoStack((current) => {
      if (!current.length) return current;
      const [restored, ...remaining] = current;
      setStrokes((drawn) => [...drawn, restored]);
      return remaining;
    });
  };

  const clearSymbolDrawing = () => {
    setRedoStack((current) => [...strokes.slice().reverse(), ...current]);
    setStrokes([]);
  };

  const saveSymbol = () => {
    const symbolAsset = buildSymbolAsset(strokes);
    const saved: SavedSymbol = {
      latex: selectedSymbol.latex,
      label: selectedSymbol.label,
      category: selectedSymbol.category,
      strokes,
      svg: symbolAsset.svg,
      width: symbolAsset.width,
      height: symbolAsset.height,
      baseline: symbolAsset.baseline,
      savedAt: Date.now(),
    };
    setSavedSymbols((current) => [saved, ...current.filter((item) => item.latex !== selectedSymbol.latex)]);
  };

  const deleteSymbol = (latex: string) => {
    setSavedSymbols((current) => current.filter((item) => item.latex !== latex));
  };

  const hasSavedSelected = savedSymbols.some((item) => item.latex === selectedSymbol.latex);

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-6 text-slate-900 font-sans">
      <header className="mb-5 max-w-[1600px] mx-auto flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <PenLine className="text-teal-600 w-7 h-7" /> Handwritten Math Editor
          </h1>
          <p className="text-slate-500 text-sm">LaTeX parser, layout engine, and editable handwritten symbol library.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button onClick={handleLoadExample} className="flex items-center gap-2 py-2 px-4 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-medium rounded-md shadow-sm">
            <FileText className="w-4 h-4" /> Load Example
          </button>
          <button onClick={handleClear} className="flex items-center gap-2 py-2 px-4 bg-white border border-slate-200 hover:bg-red-50 text-slate-700 hover:text-red-600 text-sm font-medium rounded-md shadow-sm">
            <Trash2 className="w-4 h-4" /> Clear
          </button>
          <button onClick={handleRender} disabled={isRendering || !expression.trim()} className="flex items-center gap-2 py-2 px-6 bg-teal-600 hover:bg-teal-700 disabled:bg-teal-300 text-white font-bold rounded-md shadow-sm active:scale-95">
            {isRendering ? <span className="flex items-center gap-2"><span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Rendering...</span> : <><Play className="w-4 h-4 fill-current" /> Build View</>}
          </button>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-12 gap-5">
        <section className="xl:col-span-5 flex flex-col bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden min-h-[620px]">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50">
            <span className="text-sm font-bold text-slate-700 flex items-center gap-2">
              <Code className="w-4 h-4 text-teal-600" /> Expression Editor
            </span>
            <div className="flex items-center gap-2">
              <div className="flex bg-slate-200/70 p-0.5 rounded-md text-xs">
                <button onClick={() => setMode('LaTeX')} className={`px-3 py-1 rounded ${mode === 'LaTeX' ? 'bg-white shadow-sm text-teal-700 font-bold' : 'text-slate-500'}`}>LaTeX</button>
                <button onClick={() => setMode('Tokens')} className={`px-3 py-1 rounded ${mode === 'Tokens' ? 'bg-white shadow-sm text-teal-700 font-bold' : 'text-slate-500'}`}>JSON</button>
              </div>
              <button onClick={() => setShowSettings(!showSettings)} className={`p-1.5 rounded-md ${showSettings ? 'bg-teal-50 text-teal-700' : 'text-slate-500 hover:bg-slate-100'}`}>
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2 p-3 border-b border-slate-100 bg-white">
            {symbolCatalog.filter((item) => ['Structures', 'Greek', 'Operators', 'Relations'].includes(item.category)).slice(0, 28).map((item) => (
              <button key={`${item.category}-${item.label}`} onClick={() => insertLatex(item.latex)} title={item.latex} className="min-w-10 h-9 px-2 flex items-center justify-center bg-slate-50 hover:bg-teal-50 hover:text-teal-700 border border-slate-100 rounded-md text-xs font-mono">
                {item.label}
              </button>
            ))}
          </div>

          <textarea
            id="math-input"
            value={expression}
            onChange={(event) => setExpression(event.target.value)}
            placeholder={mode === 'LaTeX' ? 'Type LaTeX here, e.g. \\begin{cases} x^2 & x>0 \\\\ 0 & x=0 \\end{cases}' : 'Enter a JSON token list...'}
            className="flex-1 w-full p-5 focus:outline-none font-mono text-base leading-relaxed resize-none bg-white placeholder-slate-300 selection:bg-teal-100"
          />

          {showSettings && (
            <div className="p-4 bg-slate-50 border-t border-slate-200 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label className="space-y-1 text-xs font-bold text-slate-500 uppercase">Variation
                <select value={variation} onChange={(event) => setVariation(event.target.value)} className="w-full p-2 bg-white border border-slate-200 rounded-md text-sm normal-case font-normal">
                  <option>Low</option><option>Medium</option><option>High</option>
                </select>
              </label>
              <label className="space-y-1 text-xs font-bold text-slate-500 uppercase">Format
                <select value={format} onChange={(event) => setFormat(event.target.value)} className="w-full p-2 bg-white border border-slate-200 rounded-md text-sm normal-case font-normal">
                  <option>SVG</option><option>PNG</option><option>PDF</option>
                </select>
              </label>
              <label className="space-y-1 text-xs font-bold text-slate-500 uppercase">Page
                <select value={pageStyle} onChange={(event) => setPageStyle(event.target.value)} className="w-full p-2 bg-white border border-slate-200 rounded-md text-sm normal-case font-normal">
                  <option>Blank</option><option>Lined</option><option>Grid</option>
                </select>
              </label>
              <label className="space-y-1 text-xs font-bold text-slate-500 uppercase">Ink
                <input type="color" value={inkColor} onChange={(event) => setInkColor(event.target.value)} className="w-full h-10 bg-white border border-slate-200 rounded-md" />
              </label>
            </div>
          )}
        </section>

        <section className="xl:col-span-7 flex flex-col bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden min-h-[620px]">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50">
            <span className="text-sm font-bold text-slate-700 flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-600" /> Output Preview
            </span>
            {result?.status === 'done' && (
              <button onClick={handleDownload} className="flex items-center gap-1.5 py-1.5 px-3 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-md">
                <Download className="w-3.5 h-3.5" /> Export {format}
              </button>
            )}
          </div>
          <div className="flex-1 bg-slate-100/60 relative overflow-hidden flex flex-col">
            {!result ? (
              <div className="m-auto flex flex-col items-center justify-center p-8 text-center text-slate-400">
                <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mb-5 shadow-sm">
                  <Play className="w-7 h-7 text-teal-100 fill-current" />
                </div>
                <h3 className="text-lg font-bold text-slate-700 mb-2">Ready to Render</h3>
                <p className="max-w-sm text-sm leading-relaxed">Compose an expression or insert one of the new structures, then build the handwritten view.</p>
              </div>
            ) : result.status === 'error' ? (
              <div className="m-auto max-w-md w-full p-6 bg-white rounded-lg shadow-sm border-l-4 border-red-500">
                <div className="flex items-start gap-4">
                  <AlertCircle className="w-6 h-6 text-red-500 shrink-0" />
                  <div>
                    <h3 className="font-bold text-slate-900">Parsing Failed</h3>
                    <p className="text-sm text-slate-600 mt-1">{result.message}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center gap-6 custom-scrollbar">
                {result.svgPages?.map((pageSvg, idx) => (
                  <div key={idx} className="w-full max-w-[800px] bg-white shadow-lg rounded-md ring-1 ring-black/5" dangerouslySetInnerHTML={{ __html: pageSvg }} />
                ))}
                <div className="sticky bottom-3 flex items-center gap-3 px-4 py-2 bg-white/95 backdrop-blur shadow-sm border border-slate-100 rounded-full text-xs font-bold">
                  <span className="flex items-center gap-1.5 text-emerald-600"><CheckCircle2 className="w-4 h-4" /> Success</span>
                  <span className="text-slate-400">Saved symbols active: {savedSymbols.length}</span>
                </div>
              </div>
            )}
          </div>
        </section>

        <section className="xl:col-span-12 bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-12">
            <div className="lg:col-span-3 border-b lg:border-b-0 lg:border-r border-slate-200 bg-slate-50 p-4">
              <h2 className="font-bold text-slate-800 mb-3">Formula Library</h2>
              <div className="flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
                {symbolCategories.map((category) => (
                  <button key={category} onClick={() => setActiveCategory(category)} className={`text-left px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap ${activeCategory === category ? 'bg-teal-600 text-white' : 'bg-white text-slate-600 border border-slate-200 hover:bg-teal-50'}`}>
                    {category}
                  </button>
                ))}
              </div>
            </div>

            <div className="lg:col-span-3 border-b lg:border-b-0 lg:border-r border-slate-200 p-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-2 gap-2 max-h-[360px] overflow-y-auto custom-scrollbar pr-1">
                {filteredSymbols.map((item) => (
                  <button key={`${item.category}-${item.latex}`} onClick={() => setSelectedSymbol(item)} className={`min-h-14 p-2 rounded-md border text-left ${selectedSymbol.latex === item.latex ? 'border-teal-500 bg-teal-50' : 'border-slate-200 bg-white hover:bg-slate-50'}`}>
                    <span className="block text-sm font-semibold text-slate-800">{item.label}</span>
                    <code className="block text-[11px] text-slate-500 truncate">{item.latex}</code>
                  </button>
                ))}
              </div>
            </div>

            <div className="lg:col-span-6 p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <div className="px-3 py-2 bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase">Original LaTeX</div>
                  <pre className="p-4 min-h-[200px] text-sm font-mono whitespace-pre-wrap break-words bg-white">{selectedSymbol.latex}</pre>
                  <button onClick={() => insertLatex(selectedSymbol.latex)} className="m-3 px-3 py-2 text-sm font-bold rounded-md bg-slate-900 text-white hover:bg-slate-800">Insert</button>
                </div>

                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <div className="px-3 py-2 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-bold text-slate-500 uppercase">Handwritten Variant</span>
                    <span className={`text-xs font-semibold ${hasSavedSelected ? 'text-emerald-600' : 'text-slate-400'}`}>{hasSavedSelected ? 'Saved' : 'Unsaved'}</span>
                  </div>
                  <div className="p-3 space-y-3">
                    <canvas
                      ref={canvasRef}
                      width={CANVAS_WIDTH}
                      height={CANVAS_HEIGHT}
                      onPointerDown={beginStroke}
                      onPointerMove={continueStroke}
                      onPointerUp={endStroke}
                      onPointerLeave={endStroke}
                      className="w-full aspect-[16/10] border border-slate-200 rounded-md touch-none cursor-crosshair bg-white"
                    />
                    <div className="flex flex-wrap items-center gap-2">
                      <button onClick={() => setTool('pen')} title="Black pen" className={`p-2 rounded-md border ${tool === 'pen' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white border-slate-200 text-slate-700'}`}><PenLine className="w-4 h-4" /></button>
                      <button onClick={() => setTool('eraser')} title="Eraser" className={`p-2 rounded-md border ${tool === 'eraser' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white border-slate-200 text-slate-700'}`}><Eraser className="w-4 h-4" /></button>
                      <button onClick={undoStroke} title="Undo" className="p-2 rounded-md border border-slate-200 bg-white text-slate-700 disabled:opacity-40" disabled={!strokes.length}><Undo2 className="w-4 h-4" /></button>
                      <button onClick={redoStroke} title="Redo" className="p-2 rounded-md border border-slate-200 bg-white text-slate-700 disabled:opacity-40" disabled={!redoStack.length}><Redo2 className="w-4 h-4" /></button>
                      <button onClick={clearSymbolDrawing} className="p-2 rounded-md border border-slate-200 bg-white text-slate-700"><Trash2 className="w-4 h-4" /></button>
                      <label className="flex items-center gap-2 text-xs text-slate-600">
                        Stroke
                        <input type="range" min="2" max="12" value={strokeSize} onChange={(event) => setStrokeSize(Number(event.target.value))} />
                      </label>
                      <div className="flex items-center gap-2 ml-auto">
                        <div className="w-12 h-12 bg-white border border-slate-200 rounded flex items-center justify-center overflow-hidden" dangerouslySetInnerHTML={{ __html: currentSymbolAsset.svg }} />
                        <button onClick={saveSymbol} disabled={!canSaveSymbol} className="flex items-center gap-2 px-3 py-2 rounded-md bg-teal-600 text-white text-sm font-bold disabled:bg-teal-300"><Save className="w-4 h-4" /> Save</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {savedSymbols.length > 0 && (
                <div className="mt-4 border border-slate-200 rounded-lg overflow-hidden">
                  <div className="px-3 py-2 bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase">Persistent Custom Symbols</div>
                  <div className="p-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-44 overflow-y-auto custom-scrollbar">
                    {savedSymbols.map((item) => (
                      <div key={item.latex} className="flex items-center gap-3 border border-slate-200 rounded-md p-2 bg-white">
                        <div className="w-12 h-12 bg-white border border-slate-100 rounded flex items-center justify-center" dangerouslySetInnerHTML={{ __html: item.svg }} />
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-semibold text-slate-800 truncate">{item.label}</div>
                          <code className="text-[11px] text-slate-500 truncate block">{item.latex}</code>
                        </div>
                        <button onClick={() => deleteSymbol(item.latex)} title="Delete symbol" className="p-2 text-slate-400 hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
