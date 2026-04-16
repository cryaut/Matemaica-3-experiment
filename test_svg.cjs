const fs = require('fs');

function parseAndScale(svgStr, targetWidth, targetHeight, targetCx, targetCy) {
    const paths = [...svgStr.matchAll(/d="([^"]+)"/g)].map(m => m[1]);
    
    let allX = [];
    let allY = [];
    for (const path of paths) {
        const coords = path.match(/[-+]?\d*\.\d+|[-+]?\d+/g);
        if (!coords) continue;
        for (let i = 0; i < coords.length; i += 2) {
            allX.push(parseFloat(coords[i]));
            allY.push(parseFloat(coords[i+1]));
        }
    }
    
    if (allX.length === 0) return "";
    
    const minX = Math.min(...allX);
    const maxX = Math.max(...allX);
    const minY = Math.min(...allY);
    const maxY = Math.max(...allY);
    
    const width = maxX - minX;
    const height = maxY - minY;
    
    const scaleX = targetWidth / width;
    const scaleY = targetHeight / height;
    const scale = Math.min(scaleX, scaleY);
    
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;
    
    const outPaths = [];
    for (const path of paths) {
        const tokens = path.split(/\s+/);
        const outTokens = [];
        let i = 0;
        while (i < tokens.length) {
            if (tokens[i].match(/[a-zA-Z]/)) {
                outTokens.push(tokens[i]);
                i++;
            } else {
                if (i + 1 >= tokens.length) break;
                const x = parseFloat(tokens[i]);
                const y = parseFloat(tokens[i+1]);
                const newX = (x - cx) * scale + targetCx;
                const newY = (y - cy) * scale + targetCy;
                outTokens.push(newX.toFixed(1));
                outTokens.push(newY.toFixed(1));
                i += 2;
            }
        }
        outPaths.push(outTokens.join(" "));
    }
    
    return outPaths;
}

const inftySvg = `
  <path style="fill: none; stroke: rgb(0, 0, 0);" d="M 27.719 42.004 C 27.211 41.496 26.392 43.853 26.226 44.35 C 25.168 47.522 27.852 52.621 31.557 51.386 C 33.942 50.591 33.726 47.436 34.328 45.629 C 35.436 42.306 39.265 35.12 42.431 34.328 C 43.408 34.084 45.346 33.121 46.482 33.689 C 51.207 36.052 53.136 44.477 47.122 46.482 C 44.779 47.263 42.516 45.657 40.512 44.989 C 37.466 43.974 34.398 42.809 31.343 41.791 C 29.65 41.227 27.192 42.048 26.226 43.497 C 25.91 43.971 25.911 45.203 25.16 45.203"></path>
`;

const arrowSvg = `
  <path style="fill: none; stroke: rgb(0, 0, 0);" d="M 23.028 42.004 C 24.211 42.004 25.27 42.071 26.439 42.217 C 27.138 42.305 27.875 42.118 28.571 42.217 C 29.635 42.369 31.109 42.703 32.196 42.431 C 33.422 42.124 34.683 41.507 35.821 40.938 C 36.19 40.754 37.334 40.938 37.74 40.938 C 39.446 40.938 41.151 40.938 42.857 40.938 C 48.756 40.938 54.655 40.938 60.554 40.938"></path>
  <path style="fill: none; stroke: rgb(0, 0, 0);" d="M 50.32 28.998 C 54.462 29.826 57.574 32.27 60.981 34.542 C 61.367 34.799 61.392 35.387 61.834 35.608 C 62.45 35.916 62.948 36.28 63.539 36.674 C 64.19 37.107 65.145 37.706 65.885 37.953 C 66.269 38.081 66.78 37.825 67.164 37.953 C 67.868 38.188 68.253 38.394 68.87 38.806 C 69.122 38.974 70.296 39.005 70.149 39.446 C 69.814 40.451 68.793 40.634 68.017 41.151 C 67.154 41.727 66.29 42.447 65.458 43.07 C 64.755 43.598 64.29 44.539 63.539 44.989 C 63.331 45.114 62.689 45.2 62.473 45.416 C 61.701 46.188 60.738 46.816 59.701 47.335 C 58.544 47.913 57.223 48.041 56.077 48.614 C 55.642 48.832 55.221 49.255 54.797 49.467 C 53.644 50.044 52.172 50.227 50.959 50.746 C 49.866 51.215 48.8 51.719 47.761 52.239"></path>
  <path style="fill: none; stroke: rgb(0, 0, 0);" d="M 54.584 30.064 C 54.584 38.024 54.584 45.984 54.584 53.945"></path>
`;

const sigmaSvg = `
  <path style="fill: none; stroke: rgb(0, 0, 0);" d="M 58.635 26.439 C 57.575 25.379 57.996 23.202 57.996 21.748 C 57.996 21.678 57.903 20.33 57.996 20.256 C 58.295 20.017 59.062 20.212 59.062 19.829 C 57.659 19.829 56.574 20.199 55.224 20.469 C 52.583 20.997 49.787 21.082 47.122 21.748 C 45.137 22.245 43.161 22.693 41.151 23.028 C 40.421 23.149 39.545 23.028 38.806 23.028 C 36.958 23.028 35.11 23.028 33.262 23.028 C 32.694 23.028 32.121 23.098 31.557 23.028 C 31.266 22.991 30.982 22.907 30.704 22.814 C 30.553 22.764 30.277 22.442 30.277 22.601 C 30.277 23.789 32.08 24.956 32.836 25.586 C 33.543 26.176 33.321 26.255 34.115 26.652 C 34.545 26.867 34.809 26.799 35.181 27.079 C 35.702 27.47 36.518 28.017 36.887 28.571 C 37.777 29.907 38.28 31.67 39.446 32.836 C 40.982 34.373 43.558 35.304 44.563 37.313 C 44.925 38.037 45.608 38.562 46.055 39.232 C 46.4 39.749 46.842 39.775 46.695 40.512 C 46.506 41.455 45.578 42.151 44.989 42.857 C 43.908 44.154 43.123 45.416 41.791 46.482 C 40.682 47.369 39.928 49.016 39.019 50.107 C 38.321 50.945 37.304 51.564 36.461 52.239 C 34.543 53.772 37.214 51.699 35.821 53.092 C 34.484 54.428 32.705 55.666 31.13 56.716 C 30.397 57.205 30.116 57.704 29.638 58.422 C 29.376 58.815 28.767 58.883 28.571 59.275 C 28.442 59.534 28.454 60.053 28.358 60.341 C 28.286 60.557 27.875 61.251 27.719 61.407 C 27.719 61.407 27.292 61.407 27.292 61.407 C 27.944 62.059 28.799 61.834 29.638 61.834 C 31.557 61.834 33.475 61.834 35.394 61.834 C 39.211 61.834 43.165 62.156 46.908 61.407 C 48.017 61.186 49.418 61.407 50.533 61.407 C 53.021 61.407 55.508 61.407 57.996 61.407 C 55.569 56.552 58.061 64.375 56.93 60.981 C 56.68 60.231 57.14 59.498 57.356 58.849 C 57.461 58.534 57.276 58.103 57.356 57.783 C 57.593 56.833 57.735 56.325 57.143 55.437"></path>
`;

console.log("INFTY:");
for (const p of parseAndScale(inftySvg, 16, 12, 12, 16)) {
    console.log('<path d="' + p + '" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>');
}

console.log("\\nARROW:");
for (const p of parseAndScale(arrowSvg, 16, 12, 12, 16)) {
    console.log('<path d="' + p + '" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>');
}

console.log("\\nSIGMA:");
for (const p of parseAndScale(sigmaSvg, 16, 16, 13, 12)) {
    console.log('<path d="' + p + '" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>');
}
