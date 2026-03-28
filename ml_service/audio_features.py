import librosa
import numpy as np
import soundfile as sf
import subprocess
import os
import tempfile

def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio format (webm, ogg, mp4) to WAV using ffmpeg.
    Returns path to the converted WAV file.
    """
    output_path = input_path.replace(
        os.path.splitext(input_path)[1], "_converted.wav"
    )

    command = [
        "ffmpeg",
        "-y",                  # overwrite if exists
        "-i", input_path,      # input file
        "-ar", "16000",        # sample rate 16kHz
        "-ac", "1",            # mono channel
        "-f", "wav",           # output format
        output_path
    ]

    print(f"🔄 Converting audio to WAV...")
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        error_msg = result.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"FFmpeg conversion failed: {error_msg}")

    print(f"✅ Converted to WAV: {output_path}")
    return output_path


def extract_features(audio_path: str) -> dict:
    """
    Extract comprehensive audio features using librosa.
    Automatically converts non-WAV formats first.
    """

    # ── Convert to WAV if needed ───────────────────────────────
    ext = os.path.splitext(audio_path)[1].lower()
    wav_path = audio_path
    converted = False

    if ext != ".wav":
        wav_path  = convert_to_wav(audio_path)
        converted = True

    try:
        # ── Load audio ─────────────────────────────────────────
        y, sr = librosa.load(wav_path, sr=16000, mono=True)

        duration = librosa.get_duration(y=y, sr=sr)
        print(f"   Duration: {duration:.2f}s, Sample rate: {sr}Hz, Samples: {len(y)}")

        if duration < 0.5:
            raise ValueError("Audio too short (< 0.5s). Please record longer.")

       # ── 1. Pitch (basic) ───────────────────────────────────
        pitches, magnitudes = librosa.piptrack(
            y=y, sr=sr, fmin=75, fmax=400
        )
        mag_threshold = np.median(magnitudes[magnitudes > 0]) \
            if magnitudes.max() > 0 else 0
        voiced = pitches[magnitudes > mag_threshold]
        voiced = voiced[voiced > 50]

        pitch_mean = float(np.mean(voiced)) if len(voiced) > 0 else 0.0
        pitch_std  = float(np.std(voiced))  if len(voiced) > 1 else 0.0

        # ── 1b. Pitch Dynamics (expressiveness) ────────────────
        if len(voiced) > 10:
            # Pitch range: difference between 90th and 10th percentile
            # Ignores extreme outliers unlike max-min
            pitch_p10   = float(np.percentile(voiced, 10))
            pitch_p90   = float(np.percentile(voiced, 90))
            pitch_range = float(pitch_p90 - pitch_p10)

            # Pitch contour: split into 8 segments, track how pitch moves
            # Measures whether the speaker goes up/down expressively
            p_seg_len   = max(len(voiced) // 8, 1)
            p_segments  = [
                float(np.mean(voiced[i * p_seg_len:(i + 1) * p_seg_len]))
                for i in range(8)
            ]

            # Pitch movement: average absolute change between segments
            # High value = expressive, dynamic pitch changes
            pitch_movement = float(np.mean(
                [abs(p_segments[i+1] - p_segments[i])
                 for i in range(len(p_segments)-1)]
            ))

            # Pitch direction changes: how often pitch reverses direction
            # Natural speech has frequent ups and downs
            directions = [
                1 if p_segments[i+1] > p_segments[i] else -1
                for i in range(len(p_segments)-1)
            ]
            direction_changes = sum(
                1 for i in range(len(directions)-1)
                if directions[i] != directions[i+1]
            )
            # Normalise to 0-1 (max possible = len(directions)-1)
            pitch_dynamism = float(
                direction_changes / max(len(directions)-1, 1)
            )

            # Pitch inflection rate: fraction of frames where pitch
            # changes by more than 20 Hz (noticeable inflection)
            pitch_diffs      = np.abs(np.diff(voiced))
            inflection_rate  = float(
                np.sum(pitch_diffs > 20) / max(len(pitch_diffs), 1)
            )

        else:
            # Not enough voiced frames — likely very quiet or short
            pitch_range      = 0.0
            pitch_movement   = 0.0
            pitch_dynamism   = 0.0
            inflection_rate  = 0.0

        # ── 2. Energy (basic) ──────────────────────────────────
        rms         = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        energy_mean = float(np.mean(rms))
        energy_std  = float(np.std(rms))

        # ── 3. Pauses ──────────────────────────────────────────
        silence_threshold = energy_mean * 0.10
        silent_frames     = np.sum(rms < silence_threshold)
        pause_ratio       = float(silent_frames / len(rms))

        # ── 3b. Energy Dynamics (loud/soft variation) ──────────
        # Split RMS into 10 equal segments, measure variation across them
        # A good speaker varies energy — quiet for setup, loud for emphasis
        n_segments    = 10
        seg_len       = max(len(rms) // n_segments, 1)
        seg_means     = [
            float(np.mean(rms[i * seg_len:(i + 1) * seg_len]))
            for i in range(n_segments)
        ]

        # Dynamic range: ratio of loudest to quietest segment
        seg_max       = max(seg_means)
        seg_min       = min(seg_means) + 1e-8   # avoid div by zero
        dynamic_range = float(seg_max / seg_min)

        # Coefficient of variation: std/mean of segment energies
        # Higher = more varied energy throughout the speech
        energy_cv     = float(np.std(seg_means) / (np.mean(seg_means) + 1e-8))

        # Emphasis ratio: fraction of frames with energy > 1.5x mean
        # Measures how often the speaker raises their voice for emphasis
        emphasis_frames  = np.sum(rms > energy_mean * 1.5)
        emphasis_ratio   = float(emphasis_frames / len(rms))

        # Energy entropy: measures how unpredictable energy changes are
        # High entropy = more natural, varied delivery
        rms_norm         = rms / (np.sum(rms) + 1e-8)
        energy_entropy   = float(-np.sum(rms_norm * np.log(rms_norm + 1e-8)))
        # Normalise entropy to 0-1 range
        max_entropy      = float(np.log(len(rms)))
        energy_entropy_n = float(energy_entropy / (max_entropy + 1e-8))

        # ── 4. Spectral Features ───────────────────────────────
        spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spec_rolloff  = librosa.feature.spectral_rolloff(y=y,  sr=sr)[0]
        zcr           = librosa.feature.zero_crossing_rate(y)[0]

        # ── 5. MFCCs ───────────────────────────────────────────
        mfccs      = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_means = mfccs.mean(axis=1).tolist()

        # ── 6. Speaking Rate ───────────────────────────────────
        onset_frames      = librosa.onset.onset_detect(y=y, sr=sr, units="time")
        num_onsets        = len(onset_frames)
        estimated_words   = num_onsets / 1.5 / 1.4
        speaking_rate_wpm = (estimated_words / duration) * 60 if duration > 0 else 0
        speaking_rate_wpm = max(40, min(250, speaking_rate_wpm))

        return {
            # ── ML model inputs ────────────────────────────────
            "speaking_rate":     round(speaking_rate_wpm,             1),
            "pause_ratio":       round(pause_ratio,                   3),
            "pitch_mean":        round(pitch_mean,                    2),
            "pitch_std":         round(pitch_std,                     2),
            "energy_mean":       round(energy_mean,                   5),
            "energy_std":        round(energy_std,                    5),

            # ── Energy dynamics ────────────────────────────────
            "dynamic_range":     round(dynamic_range,                 3),
            "energy_cv":         round(energy_cv,                     3),
            "emphasis_ratio":    round(emphasis_ratio,                3),
            "energy_entropy_n":  round(energy_entropy_n,              4),
            "seg_means":         [round(s, 5) for s in seg_means],

            # ── Pitch dynamics ─────────────────────────────────
            "pitch_range":       round(pitch_range,                   2),
            "pitch_movement":    round(pitch_movement,                2),
            "pitch_dynamism":    round(pitch_dynamism,                3),
            "inflection_rate":   round(inflection_rate,               3),

            # ── Dashboard display ──────────────────────────────
            "duration":          round(duration,                      2),
            "num_onsets":        int(num_onsets),
            "spectral_centroid": round(float(np.mean(spec_centroid)), 2),
            "spectral_rolloff":  round(float(np.mean(spec_rolloff)),  2),
            "zero_crossing_rate":round(float(np.mean(zcr)),          4),
            "mfcc_means":        [round(m, 3) for m in mfcc_means],
            "rms_values":        [round(float(r), 5) for r in rms[:100]],
        }

    finally:
        # Clean up converted WAV file
        if converted and os.path.exists(wav_path):
            os.unlink(wav_path)
            print(f"🗑️ Cleaned up converted WAV file.")
