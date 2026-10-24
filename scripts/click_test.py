"""Output latency of a playback device: play noise bursts, record them with the MacBook microphone.

    uv run --group audio python scripts/click_test.py --output "<headphone name>"

Hold the headphone against the microphone. The MacBook speaker is measured too, as
the baseline of the loopback runs; the difference is the headphone's extra latency.
"""

import argparse
import statistics
import time

import numpy as np

from tilavet.audio import SAMPLE_RATE
from tilavet.eval import estimate_offset
from tilavet.live.devices import Microphone, outputs, play

SPEAKER = "MacBook Pro Hoparlörü"
MICROPHONE = "MacBook Pro Mikrofonu"
LEAD_S = 1.0
TAIL_S = 1.0
BURST_S = 0.3
GAP_S = 0.7
BURSTS = 5
REPEATS = 3
AMPLITUDE = 0.5
MIN_SNR_DB = 10.0  # below this the recording did not hear the device


def _signal() -> np.ndarray:
    rng = np.random.default_rng(0)
    burst = AMPLITUDE * rng.uniform(-1, 1, round(BURST_S * SAMPLE_RATE))
    gap = np.zeros(round(GAP_S * SAMPLE_RATE))
    return np.concatenate([np.concatenate([burst, gap]) for _ in range(BURSTS)]).astype(np.float32)


def _measure(device: str, signal: np.ndarray) -> tuple[float, float]:
    """(latency after LEAD_S, SNR dB of the recorded signal over room noise)."""
    with Microphone(MICROPHONE) as mic:
        time.sleep(LEAD_S)
        play(signal, device)
        time.sleep(TAIL_S)

    chunks = []
    while not mic.chunks.empty():
        chunks.append(mic.chunks.get_nowait()[0])
    recording = np.concatenate(chunks)

    offset = estimate_offset(signal, recording, SAMPLE_RATE, LEAD_S + 1)
    start = round(offset * SAMPLE_RATE)
    heard = recording[start : start + len(signal)]
    noise = recording[: round(0.8 * LEAD_S * SAMPLE_RATE)]
    snr = 10 * np.log10(np.mean(heard**2) / max(float(np.mean(noise**2)), 1e-12))
    return offset - LEAD_S, float(snr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="headphone device name")
    args = parser.parse_args()

    if args.output not in outputs():
        raise SystemExit(f"no output named {args.output!r}; available: {outputs()}")

    signal = _signal()
    latency = {}
    for device in (SPEAKER, args.output):
        runs = [_measure(device, signal) for _ in range(REPEATS)]
        for lag, snr in runs:
            print(f"{device}: {lag * 1000:.0f} ms, SNR {snr:.1f} dB")
        if min(snr for _, snr in runs) < MIN_SNR_DB:
            raise SystemExit(f"{device}: microphone barely heard it; hold it closer and retry")
        latency[device] = statistics.median(lag for lag, _ in runs)

    extra = latency[args.output] - latency[SPEAKER]
    print(f"median: speaker {latency[SPEAKER] * 1000:.0f} ms, {args.output} {latency[args.output] * 1000:.0f} ms, "
          f"extra {extra * 1000:.0f} ms")


if __name__ == "__main__":
    main()
