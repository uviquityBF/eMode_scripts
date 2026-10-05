"""Shared helpers for this folder's plotting scripts (plot_crossing.py, plot_geometry.py)."""

import time


def savefig_retry(fig, out_path, attempts=5, delay_s=0.4, **kwargs):
    """fig.savefig() with retries -- this repo lives under Documents, where OneDrive's cloud-
    filter driver has been observed to transiently lock a just-created PNG during a fast
    sequential-write loop (OSError: [Errno 22] Invalid argument), not deterministically
    reproducible and not caused by anything in this code. Not a fix for a real lock (e.g. the
    file genuinely open elsewhere) -- that will still fail after `attempts`."""
    last = None
    for i in range(attempts):
        try:
            fig.savefig(out_path, **kwargs)
            return
        except OSError as e:
            last = e
            time.sleep(delay_s * (i + 1))
    raise last
