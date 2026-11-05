"""Rend les graphiques témoins, leurs planches de simulation des dyschromatopsies et la capture Streamlit.

Usage : uv run --group specimens python -I specimens/graphiques/rendre.py [--sans-streamlit] [--sans-plotly]

Toutes les couleurs viennent de `dist/` ou de `jetons.charger()`. Écrit dans `specimens/graphiques/rendus/`.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CHARTE = RACINE / "skills" / "charte"
sys.path.insert(0, str(CHARTE / "outils"))

import numpy as np  # noqa: E402
from couleurs import MACHADO, contraste  # noqa: E402
from jetons import THEMES, charger  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

DIST = CHARTE / "dist"
POLICES = CHARTE / "polices"
SORTIE = Path(__file__).resolve().parent / "rendus"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
J = charger()
SERIES = ["Série 1", "Série 2", "Série 3", "Série 4"]


def _hex(rvb) -> str:
    return "#" + "".join(f"{int(x):02X}" for x in rvb)


def simuler_image(img: Image.Image, vision: str) -> Image.Image:
    """Machado 2009 pixel par pixel (mêmes matrices et même gamma que `couleurs.simule`)."""
    a = np.asarray(img.convert("RGB"), dtype=float) / 255
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    v = np.clip(lin @ np.array(MACHADO[vision]).T, 0, 1)
    s = np.where(v <= 0.0031308, 12.92 * v, 1.055 * np.maximum(v, 1e-9) ** (1 / 2.4) - 0.055)
    return Image.fromarray(np.round(s * 255).astype(np.uint8), "RGB")


def planche(png: Path, theme: str) -> Path:
    """Original + protanopie + deutéranopie + tritanopie, en grille 2×2."""
    src = Image.open(png).convert("RGB")
    w, h = src.size
    tw = 600
    th = round(h * tw / w)
    police = ImageFont.truetype(str(POLICES / "atkinson-hyperlegible-latin-700-normal.ttf"), 16)
    bandeau = 28
    out = Image.new("RGB", (tw * 2, (th + bandeau) * 2), J[theme]["fond"])
    d = ImageDraw.Draw(out)
    for k, vision in enumerate(("normale", *MACHADO)):
        im = src if vision == "normale" else simuler_image(src, vision)
        x, y = (k % 2) * tw, (k // 2) * (th + bandeau)
        d.text((x + 8, y + 4), vision, fill=J[theme]["texte"], font=police)
        out.paste(im.resize((tw, th), Image.LANCZOS), (x, y + bandeau))
    cible = png.with_name(png.stem + "-simulation.png")
    out.quantize(colors=128, dither=Image.Dither.NONE).save(cible, optimize=True)  # poids : ~2 Mo au total
    return cible


# ---------------------------------------------------------------- matplotlib
def carte_sequentielle(theme: str):
    """Aucune palette séquentielle dans les jetons (constat) : dégradé `surface-alt` vers `primaire`, fait pour ce témoin."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("sequentielle", [J[theme]["surface-alt"], J[theme]["primaire"]])


def rendre_matplotlib(theme: str) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    for ttf in POLICES.glob("*.ttf"):
        font_manager.fontManager.addfont(str(ttf))
    plt.style.use(DIST / f"charte-{theme}.mplstyle")
    t = J[theme]
    rng = np.random.default_rng(7)
    fichiers = []

    def sauver(fig, nom):
        p = SORTIE / f"mpl-{nom}-{theme}.png"
        fig.savefig(p, dpi=100)
        plt.close(fig)
        fichiers.append(p)

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(5)
    for k in range(4):
        ax.bar(x + (k - 1.5) * 0.2, rng.uniform(3, 9, 5), 0.2, label=SERIES[k])
    ax.set_xticks(x, [f"T{n}" for n in range(1, 6)])
    ax.set_title("Barres groupées, 4 séries")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.08), frameon=False)
    sauver(fig, "barres")

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(12)
    for k in range(8):
        y = np.cumsum(rng.normal(0.3, 1, 12)) + k * 2
        ax.plot(x, y, linewidth=2, color=t[f"cat-{k + 1}"])
        ax.annotate(f"Série {k + 1}", (x[-1], y[-1]), xytext=(6, 0), textcoords="offset points", va="center",
                    color=t["texte"], fontsize=11)
    ax.set_xlim(0, 13.5)
    ax.set_title("Lignes, 8 séries, légende directe")
    sauver(fig, "lignes")

    fig, ax = plt.subplots(figsize=(10, 6))
    for k in range(4):
        cx, cy = rng.uniform(2, 8, 2)
        ax.scatter(rng.normal(cx, 1, 40), rng.normal(cy, 1, 40), s=45, label=SERIES[k], edgecolors=t["surface"], linewidths=0.8)
    ax.set_title("Nuage de points, 4 séries")
    ax.legend(frameon=False)
    sauver(fig, "nuage")

    fig, ax = plt.subplots(figsize=(10, 6))
    m = ax.imshow(rng.uniform(0, 1, (8, 12)), cmap=carte_sequentielle(theme), aspect="auto")
    ax.grid(False)
    ax.set_title("Carte de chaleur séquentielle (dégradé fait pour le témoin)")
    fig.colorbar(m, ax=ax)
    sauver(fig, "chaleur")
    return fichiers


# ---------------------------------------------------------------- plotly
def rendre_plotly(theme: str) -> list[Path]:
    import plotly.graph_objects as go
    import plotly.io as pio
    if not os.environ.get("BROWSER_PATH") and CHROME.exists():
        os.environ["BROWSER_PATH"] = str(CHROME)
    gabarit = go.layout.Template(json.loads((DIST / f"plotly-{theme}.json").read_text(encoding="utf-8")))
    rng = np.random.default_rng(11)
    fichiers = []
    barres = go.Figure([go.Bar(name=SERIES[k], x=[f"T{n}" for n in range(1, 6)], y=rng.uniform(3, 9, 5)) for k in range(4)])
    barres.update_layout(barmode="group", title="Barres groupées (plotly)")
    lignes = go.Figure([go.Scatter(name=f"Série {k + 1}", x=list(range(12)), y=np.cumsum(rng.normal(0.3, 1, 12)) + 2 * k, mode="lines")
                        for k in range(8)])
    lignes.update_layout(title="Lignes, 8 séries (plotly)")
    nuage = go.Figure([go.Scatter(name=SERIES[k], x=rng.normal(rng.uniform(2, 8), 1, 40), y=rng.normal(rng.uniform(2, 8), 1, 40),
                                  mode="markers") for k in range(4)])
    nuage.update_layout(title="Nuage de points (plotly)")
    for nom, fig in (("barres", barres), ("lignes", lignes), ("nuage", nuage)):
        fig.update_layout(template=gabarit)
        p = SORTIE / f"plotly-{nom}-{theme}.png"
        pio.write_image(fig, p, width=1000, height=600)
        fichiers.append(p)
    return fichiers


# ---------------------------------------------------------------- streamlit
def navigateur() -> Path:
    return next(p for p in (EDGE, CHROME) if p.exists())


def capturer(url: str, cible: Path, attente: float = 8.0) -> None:
    """Capture par le protocole DevTools (Edge headless) : `--screenshot` seul part avant que Streamlit ait rendu la page."""
    import asyncio
    import base64

    from websockets.asyncio.client import connect  # présent via Streamlit (non déclaré)

    cdp = "9333"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
        nav = subprocess.Popen([str(navigateur()), "--headless=new", f"--user-data-dir={prof}", f"--remote-debugging-port={cdp}",
                                "--window-size=1100,900", "--hide-scrollbars", "about:blank"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        async def aller() -> None:
            for _ in range(60):
                try:
                    cibles = json.load(urllib.request.urlopen(f"http://localhost:{cdp}/json", timeout=1))
                    page = next(c for c in cibles if c["type"] == "page")
                    break
                except (OSError, StopIteration):
                    await asyncio.sleep(0.5)
            else:
                raise RuntimeError("DevTools indisponible")
            ws = await connect(page["webSocketDebuggerUrl"], max_size=64 * 1024 * 1024)

            async def cmd(i: int, methode: str, **params):
                await ws.send(json.dumps({"id": i, "method": methode, "params": params}))
                while True:
                    m = json.loads(await ws.recv())
                    if m.get("id") == i:
                        return m.get("result")

            await cmd(1, "Emulation.setDeviceMetricsOverride", width=1100, height=900, deviceScaleFactor=1, mobile=False)
            await cmd(2, "Page.navigate", url=url)
            await asyncio.sleep(attente)
            r = await cmd(3, "Page.captureScreenshot", format="png")
            cible.write_bytes(base64.b64decode(r["data"]))
            await ws.close()

        try:
            asyncio.run(aller())
        finally:
            nav.terminate()
            try:
                nav.wait(10)
            except subprocess.TimeoutExpired:
                nav.kill()


def rendre_streamlit(theme: str = "sombre") -> list[Path]:
    """Lance l'appli avec un `.streamlit/config.toml` temporaire (copie de `dist/streamlit-<theme>.toml`), capture en navigateur headless."""
    port = "8599"
    cible = SORTIE / f"streamlit-{theme}.png"
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        (Path(tmp) / ".streamlit").mkdir()
        shutil.copy(DIST / f"streamlit-{theme}.toml", Path(tmp) / ".streamlit" / "config.toml")
        t0 = time.time()
        serveur = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(Path(__file__).with_name("streamlit_demo.py")), "--server.headless", "true",
             "--server.port", port, "--browser.gatherUsageStats", "false"],
            cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            while True:
                try:
                    urllib.request.urlopen(f"http://localhost:{port}/_stcore/health", timeout=1)
                    break
                except OSError:
                    if time.time() - t0 > 30:
                        print("Streamlit : démarrage > 30 s, capture non faite")
                        return []
                    time.sleep(0.5)
            print(f"Streamlit : prêt en {time.time() - t0:.1f} s")
            capturer(f"http://localhost:{port}", cible)
        finally:
            serveur.terminate()
            try:
                serveur.wait(10)
            except subprocess.TimeoutExpired:
                serveur.kill()
    return [cible] if cible.exists() else []


def mesurer_bouton(png: Path, theme: str = "sombre") -> None:
    """Contraste réel du bouton principal : fond = pixels égaux à `primaire`, libellé = pixel le plus clair de la zone."""
    a = np.asarray(Image.open(png).convert("RGB"))
    prim = np.array([int(J[theme]["primaire"][i:i + 2], 16) for i in (1, 3, 5)])
    ys, xs = np.nonzero(np.abs(a.astype(int) - prim).sum(axis=2) < 6)
    if not len(ys):
        print("Bouton principal introuvable dans la capture")
        return
    garde = (ys < ys.min() + 60) & (xs < xs.min() + 200)  # le bouton : le graphique en dessous réutilise `primaire` (cat-1)
    ys, xs = ys[garde], xs[garde]
    zone = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].reshape(-1, 3)
    fond, libelle = _hex(prim), _hex(zone[zone.sum(axis=1).argmax()])
    print(f"Bouton principal : fond {fond}, libellé {libelle}, contraste {contraste(fond, libelle):.2f}:1 "
          f"(zone x {xs.min()}-{xs.max()}, y {ys.min()}-{ys.max()}) ; fond du bouton sur `fond` {contraste(fond, J[theme]['fond']):.2f}:1")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument("--sans-streamlit", action="store_true")
    p.add_argument("--sans-plotly", action="store_true")
    args = p.parse_args(argv)
    SORTIE.mkdir(exist_ok=True)
    pngs: list[tuple[Path, str]] = []
    for theme in THEMES:
        pngs += [(f, theme) for f in rendre_matplotlib(theme)]
        if not args.sans_plotly:
            pngs += [(f, theme) for f in rendre_plotly(theme)]
    for f, theme in pngs:
        planche(f, theme)
    if not args.sans_streamlit:
        for f in rendre_streamlit("sombre"):
            mesurer_bouton(f)
    total = sum(f.stat().st_size for f in SORTIE.glob("*.png"))
    print(f"{len(list(SORTIE.glob('*.png')))} PNG, {total / 1e6:.2f} Mo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
