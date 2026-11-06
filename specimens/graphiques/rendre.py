"""Rend les graphiques témoins, leurs planches de simulation des dyschromatopsies et la capture Streamlit.

Usage : uv run --group specimens python -I specimens/graphiques/rendre.py [--sans-streamlit] [--sans-plotly]

Toutes les couleurs viennent de `dist/` ou de `jetons.charger()`. Écrit dans `specimens/graphiques/rendus/`.
Règles appliquées (charte v2.1) : étiquette directe dès deux séries en clair et au-delà de quatre en sombre, placée
sans chevauchement (`placement.placer`) ; un motif par série (tirets, marqueurs, hachures : `MOTIFS` de
`dist/charte.py`) ; palettes `seq` et `div` pour les aplats contigus ; Streamlit sans `type="primary"`.
"""
from __future__ import annotations

import argparse
import importlib.util
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
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from couleurs import MACHADO, contraste  # noqa: E402
from jetons import THEMES, charger  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from placement import placer  # noqa: E402

DIST = CHARTE / "dist"
POLICES = CHARTE / "polices"
SORTIE = Path(__file__).resolve().parent / "rendus"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
J = charger()
SERIES = ["Série 1", "Série 2", "Série 3", "Série 4"]
_spec = importlib.util.spec_from_file_location("charte_dist", DIST / "charte.py")
CHARTE_PY = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CHARTE_PY)
MOTIFS = CHARTE_PY.MOTIFS
TAILLE_ETIQUETTE = 11  # pt, étiquettes directes matplotlib


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


def _hex(rvb) -> str:
    return "#" + "".join(f"{int(x):02X}" for x in rvb)


# ---------------------------------------------------------------- matplotlib
def carte(theme: str, palette: str):
    """Palette discrète des jetons `seq` ou `div` (cinq pas, aplats contigus)."""
    from matplotlib.colors import ListedColormap
    return ListedColormap(J[theme][palette], name=palette)


def etiquettes_directes(ax, x: float, ys: list[float], noms: list[str], couleurs: list[str], taille: float) -> None:
    """Étiquette en bout de ligne, sans chevauchement : écart minimal d'une hauteur de ligne (1,25 × taille), en points."""
    ax.get_ylim()  # fige l'échelle avant la conversion en points
    fig = ax.figure
    pts = [ax.transData.transform((x, y))[1] * 72 / fig.dpi for y in ys]
    for nom, couleur, y, y0, cible in zip(noms, couleurs, ys, pts, placer(pts, taille * 1.25), strict=True):
        ax.annotate(nom, (x, y), xytext=(8, cible - y0), textcoords="offset points", va="center", color=couleur,
                    fontsize=taille, fontweight="bold")


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
        barres = ax.bar(x + (k - 1.5) * 0.2, rng.uniform(3, 9, 5), 0.2, label=SERIES[k], hatch=MOTIFS["mpl_hatch"][k],
                        edgecolor=t["surface"], linewidth=0.8)
        ax.bar_label(barres, [f"S{k + 1}"] + [""] * 4, padding=3, color=t["texte"], fontsize=TAILLE_ETIQUETTE, fontweight="bold")
    ax.set_xticks(x, [f"T{n}" for n in range(1, 6)])
    ax.set_title("Barres groupées, 4 séries : hachures et étiquettes directes")
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.08), frameon=False)
    sauver(fig, "barres")

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(12)
    fins = []
    for k in range(8):
        y = np.cumsum(rng.normal(0.3, 1, 12)) + k * 2
        ax.plot(x, y, markevery=[len(x) - 1])  # couleur, tiret et marqueur viennent du cycle du style
        fins.append(y[-1])
    ax.set_xlim(0, 13.5)
    etiquettes_directes(ax, x[-1], fins, [f"Série {k + 1}" for k in range(8)], [t[f"cat-{k + 1}"] for k in range(8)], TAILLE_ETIQUETTE)
    ax.set_title("Lignes, 8 séries : tirets, marqueurs, étiquettes directes sans chevauchement")
    sauver(fig, "lignes")

    fig, ax = plt.subplots(figsize=(10, 6))
    for k in range(4):
        cx, cy = rng.uniform(2, 8, 2)
        xs, ys = rng.normal(cx, 1, 40), rng.normal(cy, 1, 40)
        ax.scatter(xs, ys, s=45, label=SERIES[k], marker=MOTIFS["mpl_marker"][k], edgecolors=t["surface"], linewidths=0.8)
        ax.annotate(SERIES[k], (xs.mean(), ys.max()), xytext=(0, 8), textcoords="offset points", ha="center", color=t["texte"],
                    fontsize=TAILLE_ETIQUETTE, fontweight="bold")
    ax.set_title("Nuage de points, 4 séries : marqueurs et étiquettes directes")
    ax.legend(frameon=False)
    sauver(fig, "nuage")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.5))
    for ax_, palette, valeurs, titre in ((a1, "seq", rng.uniform(0, 1, (6, 8)), "Séquentielle (seq-1 à seq-5)"),
                                         (a2, "div", rng.uniform(-1, 1, (6, 8)), "Divergente (div-1 à div-5)")):
        borne = (0, 1) if palette == "seq" else (-1, 1)
        m = ax_.imshow(valeurs, cmap=carte(theme, palette), vmin=borne[0], vmax=borne[1], aspect="auto")
        ax_.grid(False)
        ax_.set_title(titre)
        for (i, k), v in np.ndenumerate(valeurs):  # valeur écrite dans chaque cellule (A6)
            cellule = _hex(np.round(np.array(m.cmap(m.norm(v))[:3]) * 255))
            encre = max((J["clair"]["texte"], J["sombre"]["texte"]), key=lambda e: contraste(e, cellule))  # le plus contrasté
            ax_.text(k, i, f"{v + 0.0:.1f}".replace(".", ",").replace("-0,0", "0,0"), ha="center", va="center", fontsize=9, color=encre)
        fig.colorbar(m, ax=ax_, ticks=np.linspace(*borne, 6))
    fig.suptitle("Cartes de chaleur : palettes des jetons, valeur dans chaque cellule", color=t["texte"])
    sauver(fig, "chaleur")
    return fichiers


# ---------------------------------------------------------------- plotly
def rendre_plotly(theme: str) -> list[Path]:
    import plotly.graph_objects as go
    import plotly.io as pio
    if not os.environ.get("BROWSER_PATH") and CHROME.exists():
        os.environ["BROWSER_PATH"] = str(CHROME)
    gabarit = go.layout.Template(json.loads((DIST / f"plotly-{theme}.json").read_text(encoding="utf-8")))
    t = J[theme]
    rng = np.random.default_rng(11)
    fichiers = []
    largeur, hauteur, marges = 1000, 600, {"l": 60, "r": 120, "t": 80, "b": 60}
    # motifs trace par trace (les tirets et marqueurs ne passent pas par le gabarit) : MOTIFS de dist/charte.py
    barres = go.Figure([go.Bar(name=SERIES[k], x=[f"T{n}" for n in range(1, 6)], y=rng.uniform(3, 9, 5), text=[f"S{k + 1}"] * 5,
                               textposition="inside", insidetextanchor="end", textfont={"color": t["texte"], "size": 13},
                               marker={"pattern": {"shape": MOTIFS["plotly_pattern"][k], "fgcolor": t["surface"]}}) for k in range(4)])
    barres.update_layout(barmode="group", title="Barres groupées (plotly) : hachures et étiquettes directes")
    series = [np.cumsum(rng.normal(0.3, 1, 12)) + 2 * k for k in range(8)]
    lignes = go.Figure([go.Scatter(name=f"Série {k + 1}", x=list(range(12)), y=y, mode="lines+markers",
                                   line={"dash": MOTIFS["plotly_dash"][k], "width": 2},
                                   marker={"symbol": MOTIFS["plotly_symbol"][k], "size": 7}) for k, y in enumerate(series)])
    bas, haut = min(y.min() for y in series) - 1, max(y.max() for y in series) + 1
    hauteur_trace = hauteur - marges["t"] - marges["b"]
    px_fin = [(y[-1] - bas) / (haut - bas) * hauteur_trace for y in series]
    for k, (y, y0, cible) in enumerate(zip(series, px_fin, placer(px_fin, 17), strict=True)):  # écart d'une ligne, en px
        lignes.add_annotation(x=11, y=y[-1], text=f"<b>Série {k + 1}</b>", showarrow=False, xanchor="left", xshift=10,
                              yshift=cible - y0, font={"color": t[f"cat-{k + 1}"], "size": 13})
    lignes.update_layout(title="Lignes, 8 séries (plotly) : tirets, marqueurs, étiquettes directes", showlegend=False,
                         yaxis={"range": [bas, haut]}, margin=marges)
    nuage = go.Figure([go.Scatter(name=SERIES[k], x=rng.normal(rng.uniform(2, 8), 1, 40), y=rng.normal(rng.uniform(2, 8), 1, 40),
                                  mode="markers", marker={"symbol": MOTIFS["plotly_symbol"][k], "size": 9}) for k in range(4)])
    nuage.update_layout(title="Nuage de points (plotly) : un marqueur par série")
    for nom, fig in (("barres", barres), ("lignes", lignes), ("nuage", nuage)):
        fig.update_layout(template=gabarit)
        p = SORTIE / f"plotly-{nom}-{theme}.png"
        pio.write_image(fig, p, width=largeur, height=hauteur)
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
        # poids (~2 Mo au plus pour le dossier) : 256 couleurs, sans tramage, après la planche faite sur l'original
        Image.open(f).convert("RGB").quantize(colors=256, dither=Image.Dither.NONE).save(f, optimize=True)
    if not args.sans_streamlit:
        rendre_streamlit("sombre")
    total = sum(f.stat().st_size for f in SORTIE.glob("*.png"))
    print(f"{len(list(SORTIE.glob('*.png')))} PNG, {total / 1e6:.2f} Mo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
