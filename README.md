# Pointillism Lily 🌸

A generative pointillism art simulation rendered in Python using Pygame and NumPy, deployed live to GitHub Pages.

Live Website: [https://veerasatyam.github.io/ForYou/](https://veerasatyam.github.io/ForYou/)

---

## 🎨 Overview

**Pointillism Lily** renders over 15,000 distinct particle points per frame to simulate realistic botanical growth and bloom dynamics:
- **Parametric Midrib Curves:** Petals expand along Bezier curves with dynamic curling and curvature.
- **Natural Sway & Stems:** Interpolated swaying and stem elevation based on smooth step time functions.
- **Dual-Pass Additive Glow:** Real-time scaling pass to create an ethereal, neon bloom effect.
- **Dust & Floating Spores:** Atmospheric particles and ground soil mound particles.

---

## 📁 Repository Structure

```
├── index.html            # Responsive web player for GitHub Pages
├── flower.mp4            # Pre-rendered 60 FPS / 30 FPS high-definition animation
├── poster.jpg            # Video poster preview image
├── pointillism_lily.py   # Main Pygame pointillism simulation source code
├── render_video.py       # Headless video generator (converts simulation to MP4)
├── requirements.txt      # Python dependencies (pygame, numpy, imageio)
└── README.md
```

---

## 🚀 Running Locally

### 1. Interactive Desktop Simulation
```bash
pip install -r requirements.txt
python pointillism_lily.py
```
- Press <kbd>Space</kbd> to Pause / Play.
- Press <kbd>R</kbd> to Restart.
- Press <kbd>Esc</kbd> to Exit.

### 2. Run the Web Server Locally
```bash
python -m http.server 8000
```
Then visit `http://localhost:8000` in your web browser.

---

## 🌐 GitHub Pages Deployment
1. Go to repository **Settings** → **Pages**.
2. Under **Build and deployment**, select:
   - Source: **Deploy from a branch**
   - Branch: `main` / `(root)`
3. Save, and your site will be live at:
   `https://veerasatyam.github.io/ForYou/`
