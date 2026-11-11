"""Edit This Video: graphics worker. Runs inside the private tools folder (playwright).

Opens render.html in a headless browser, draws every frame of the captions and graphics with a see-through
background using the same option library as the style page, and pipes the frames into ffmpeg.

Usage: render_worker.py <render.html> <out.mov> <fps> <duration seconds> [<chrome path>]
"""
import json
import os
import subprocess
import sys
import time
from fractions import Fraction

from playwright.sync_api import sync_playwright

W, H = 1080, 1920


def main(page_path, out, fps_str, duration, chrome):
    fps = float(Fraction(fps_str))
    n = int(round(float(duration) * fps))
    tl = json.load(open(os.path.join(os.path.dirname(os.path.dirname(page_path)), "render", "timeline.json"), encoding="utf-8"))
    spans = [(i["at"], i["at"] + i["dur"] + 0.06) for i in tl["items"]]

    def active(t):
        return any(a <= t <= b for a, b in spans)

    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", fps_str,
                           "-c:v", "png", "-i", "-", "-c:v", "png", "-pix_fmt", "rgba", out], stdin=subprocess.PIPE)
    with sync_playwright() as pw:
        kw = {"args": ["--force-color-profile=srgb", "--font-render-hinting=none"]}
        if chrome:
            kw["executable_path"] = chrome
        browser = pw.chromium.launch(**kw)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("file://" + os.path.abspath(page_path))
        page.wait_for_function("window.renderReady === true", timeout=60000)
        page.evaluate("document.fonts.ready")
        if errors:
            print("Page errors: " + " | ".join(errors))
            sys.exit(1)
        blank = None
        t0, drawn = time.time(), 0
        for k in range(n):
            t = k / fps
            if active(t):
                page.evaluate(f"window.renderAt({t:.6f})")
                png = page.screenshot(omit_background=True, type="png", clip={"x": 0, "y": 0, "width": W, "height": H})
                drawn += 1
            else:
                if blank is None:
                    page.evaluate("window.renderAt(-1)")
                    blank = page.screenshot(omit_background=True, type="png", clip={"x": 0, "y": 0, "width": W, "height": H})
                png = blank
            ff.stdin.write(png)
            if k and k % int(fps * 5) == 0:
                print(f"  {t:5.1f} s of {float(duration):.1f} s", flush=True)
        if errors:
            print("Page errors while drawing: " + " | ".join(errors[:5]))
        browser.close()
    ff.stdin.close()
    if ff.wait() != 0:
        print("ffmpeg couldn't save the graphics.")
        sys.exit(1)
    print(f"  drew {drawn} frames in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main(*sys.argv[1:5], sys.argv[5] if len(sys.argv) > 5 else "")
