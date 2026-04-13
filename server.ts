import express from "express";
import { createServer as createViteServer } from "vite";
import { spawn } from "child_process";
import path from "path";

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API Route to call the Python backend
  app.post("/api/render", (req, res) => {
    const pythonProcess = spawn("python3", ["backend_runner.py"]);
    
    let outputData = "";
    let errorData = "";

    pythonProcess.stdout.on("data", (data) => {
      outputData += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      errorData += data.toString();
    });

    pythonProcess.on("close", (code) => {
      if (code !== 0) {
        console.error("Python process exited with code", code);
        console.error("Error:", errorData);
        return res.status(500).json({ status: "error", message: "Python backend failed." });
      }
      
      try {
        const result = JSON.parse(outputData);
        res.json(result);
      } catch (e) {
        console.error("Failed to parse Python output:", outputData);
        res.status(500).json({ status: "error", message: "Invalid response from Python backend." });
      }
    });

    // Send the request body to the Python script via stdin
    pythonProcess.stdin.write(JSON.stringify(req.body));
    pythonProcess.stdin.end();
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
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
