import subprocess

import numpy as np
import pytest

from tilavet.audio import SAMPLE_RATE, load_audio


@pytest.fixture
def stereo_44k_mp3(tmp_path):
    path = tmp_path / "tone.mp3"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=1.5",
         "-ac", "2", "-ar", "44100", str(path)],
        check=True,
    )
    return path


def test_load_audio_resamples_to_16k_mono_float32(stereo_44k_mp3):
    audio = load_audio(stereo_44k_mp3)

    assert audio.dtype == np.float32
    assert audio.ndim == 1
    assert len(audio) / SAMPLE_RATE == pytest.approx(1.5, abs=0.06)
    assert 0.05 < np.abs(audio).max() <= 1.0


def test_load_audio_slice(stereo_44k_mp3):
    audio = load_audio(stereo_44k_mp3, start_s=0.5, end_s=1.0)

    assert len(audio) / SAMPLE_RATE == pytest.approx(0.5, abs=0.03)


def test_load_audio_other_rate(stereo_44k_mp3):
    audio = load_audio(stereo_44k_mp3, sample_rate=22_050)

    assert len(audio) / 22_050 == pytest.approx(1.5, abs=0.06)


def test_load_audio_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_audio(tmp_path / "missing.wav")
