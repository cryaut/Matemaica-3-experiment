import express from "express";
import { createServer as createViteServer } from "vite";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";

async function startServer() {
  const app = express();
  const PORT = Number(process.env.PORT || 3000);

  app.use(express.json());

  // Logging middleware
  app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
    next();
  });

  // Health check
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", message: "Server is running" });
  });

  // API Route to call the Python backend
  app.post("/api/render", async (req, res) => {
    console.log("Received render request:", JSON.stringify(req.body).substring(0, 100) + "...");
    
    if (!req.body || typeof req.body !== 'object') {
      return res.status(400).json({ status: "error", message: "Invalid request body" });
    }

    const scriptPath = path.join(process.cwd(), "backend_runner.py");
    
    const mingwPythonDir = "C:\\Users\\User\\Documents\\MinGW\\ucrt64\\bin";
    const pythonCandidates = [
      process.env.PYTHON,
      "C:\\Users\\User\\Documents\\MinGW\\ucrt64\\bin\\python3.exe",
      "C:\\Users\\User\\Documents\\MinGW\\ucrt64\\bin\\python.exe",
      "python3",
      "py",
      "python",
    ].filter(Boolean) as string[];

    const spawnPython = (cmd: string) => spawn(cmd, [scriptPath], {
      env: {
        ...process.env,
        PATH: `${mingwPythonDir};${process.env.PATH || ""}`,
      },
    });

    let candidateIndex = 0;
    while (candidateIndex < pythonCandidates.length && pythonCandidates[candidateIndex].includes(":\\") && !fs.existsSync(pythonCandidates[candidateIndex])) {
      candidateIndex += 1;
    }

    let pythonProcess = spawnPython(pythonCandidates[candidateIndex] || "python3");
    
    let outputData = "";
    let errorData = "";

    const setupProcess = (proc: any) => {
      proc.on("error", (err: any) => {
        if (err.code === 'ENOENT' && candidateIndex < pythonCandidates.length - 1) {
          candidateIndex += 1;
          while (candidateIndex < pythonCandidates.length && pythonCandidates[candidateIndex].includes(":\\") && !fs.existsSync(pythonCandidates[candidateIndex])) {
            candidateIndex += 1;
          }
          if (candidateIndex < pythonCandidates.length) {
            console.log(`${pythonCandidates[candidateIndex - 1]} not found, trying ${pythonCandidates[candidateIndex]}...`);
            pythonProcess = spawnPython(pythonCandidates[candidateIndex]);
            setupProcess(pythonProcess);
          }
          return;
        }
        console.error(`Failed to start Python process:`, err);
        if (!res.headersSent) {
          res.status(500).json({ status: "error", message: `Failed to start Python backend: ${err.message}` });
        }
      });

      proc.stdout.on("data", (data: any) => {
        outputData += data.toString();
      });

      proc.stderr.on("data", (data: any) => {
        errorData += data.toString();
      });

      proc.on("close", (code: number) => {
        if (code !== 0) {
          console.error("Python process exited with code", code);
          console.error("Stderr output:", errorData);
          if (!res.headersSent) {
            return res.status(500).json({ 
              status: "error", 
              message: "Python backend failed.",
              details: errorData 
            });
          }
          return;
        }
        
        try {
          const lines = outputData.trim().split('\n');
          const lastLine = lines[lines.length - 1];
          const result = JSON.parse(lastLine);
          res.json(result);
        } catch (e) {
          console.error("Failed to parse Python output. Raw output:", outputData);
          if (!res.headersSent) {
            res.status(500).json({ 
              status: "error", 
              message: "Invalid response from Python backend.",
              rawOutput: outputData.substring(0, 500)
            });
          }
        }
      });

      // Send the request body to the Python script via stdin
      try {
        proc.stdin.write(JSON.stringify(req.body));
        proc.stdin.end();
      } catch (err) {
        console.error("Error writing to Python stdin:", err);
      }
    };

    setupProcess(pythonProcess);
  });

  // Catch-all for other API routes to prevent falling through to Vite SPA handler
  app.all("/api/*", (req, res) => {
    res.status(404).json({ status: "error", message: `API route not found: ${req.method} ${req.url}` });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: {
        middlewareMode: true,
        hmr: { port: PORT + 10000 },
      },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
