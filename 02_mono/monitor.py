#!/usr/bin/env python3
"""
Realtime OpenFOAM force monitor
Reads Fx Fy Fz from force.dat and plots them live.

Usage:
    python3 monitor_forces.py

Default file:
    postProcessing/forces/0/force.dat
"""

import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

FORCE_FILE = "postProcessing/forces/0/force.dat"

REFRESH_INTERVAL = 0.5  # seconds
WINDOW = None  # None = show all data
# WINDOW = 20            # show only last 20 seconds

# ============================================================
# MATPLOTLIB SETUP
# ============================================================

plt.ion()

fig, ax = plt.subplots(figsize=(12, 6))

(line_fx,) = ax.plot([], [], label="Fx")
(line_fy,) = ax.plot([], [], label="Fy")
(line_fz,) = ax.plot([], [], label="Fz")

ax.set_xlabel("Time [s]")
ax.set_ylabel("Force [N]")
ax.set_title("OpenFOAM Forces Realtime")

ax.grid(True)
ax.legend()

# ============================================================
# DATA STORAGE
# ============================================================

times = []
fxs = []
fys = []
fzs = []

last_size = 0

# ============================================================
# PARSER
# ============================================================


def parse_force_line(line):
    """
    OpenFOAM force.dat format typically:

    Time   (Fx Fy Fz)   (Mx My Mz)

    Example:
    0.005  (1 2 3)  (0 0 0)
    """

    line = line.strip()

    if not line or line.startswith("#"):
        return None

    try:
        parts = line.split()

        t = float(parts[0])

        # Remove parentheses
        fx = float(parts[1].replace("(", ""))
        fy = float(parts[2])
        fz = float(parts[3].replace(")", ""))

        return t, fx, fy, fz

    except Exception:
        return None


# ============================================================
# MAIN LOOP
# ============================================================

force_path = Path(FORCE_FILE)

if not force_path.exists():
    raise FileNotFoundError(f"Cannot find: {FORCE_FILE}")

print(f"Monitoring: {FORCE_FILE}")

while True:

    try:
        current_size = force_path.stat().st_size

        # Read only if file changed
        if current_size != last_size:

            with open(force_path, "r") as f:
                lines = f.readlines()

            # Reset and reparse everything
            times.clear()
            fxs.clear()
            fys.clear()
            fzs.clear()

            for line in lines:
                parsed = parse_force_line(line)

                if parsed is not None:
                    t, fx, fy, fz = parsed

                    times.append(t)
                    fxs.append(fx)
                    fys.append(fy)
                    fzs.append(fz)

            # Convert to arrays
            t = np.array(times)
            fx = np.array(fxs)
            fy = np.array(fys)
            fz = np.array(fzs)

            # Optional moving window
            if WINDOW is not None and len(t) > 0:
                mask = t > (t[-1] - WINDOW)

                t = t[mask]
                fx = fx[mask]
                fy = fy[mask]
                fz = fz[mask]

            # Update plots
            line_fx.set_data(t, fx)
            line_fy.set_data(t, fy)
            line_fz.set_data(t, fz)

            ax.relim()
            ax.autoscale_view()

            fig.canvas.draw()
            fig.canvas.flush_events()

            last_size = current_size

        time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped.")
        break

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
