import numpy as np
import pandas as pd
import os

np.random.seed(42)
NUM_SAMPLES = 1000

def generate_sample(confidence_level):
    """
    Generate realistic audio + text features
    based on a given confidence level (0=low, 1=mid, 2=high)
    """

    if confidence_level == 2:  # High confidence
        speaking_rate    = np.random.normal(145, 15)   # ideal wpm
        pause_ratio      = np.random.normal(0.15, 0.05)
        pitch_mean       = np.random.normal(180, 20)
        pitch_std        = np.random.normal(30, 8)
        energy_mean      = np.random.normal(0.07, 0.015)
        energy_std       = np.random.normal(0.02, 0.005)
        filler_ratio     = np.random.normal(0.02, 0.01)
        sentiment        = np.random.normal(0.4, 0.2)
        avg_sent_length  = np.random.normal(14, 3)
        word_count       = np.random.normal(180, 40)
        label            = 2

    elif confidence_level == 1:  # Medium confidence
        speaking_rate    = np.random.normal(125, 20)
        pause_ratio      = np.random.normal(0.30, 0.08)
        pitch_mean       = np.random.normal(160, 25)
        pitch_std        = np.random.normal(20, 6)
        energy_mean      = np.random.normal(0.05, 0.012)
        energy_std       = np.random.normal(0.015, 0.004)
        filler_ratio     = np.random.normal(0.05, 0.02)
        sentiment        = np.random.normal(0.1, 0.2)
        avg_sent_length  = np.random.normal(12, 4)
        word_count       = np.random.normal(130, 35)
        label            = 1

    else:  # Low confidence
        speaking_rate    = np.random.normal(95, 25)
        pause_ratio      = np.random.normal(0.50, 0.10)
        pitch_mean       = np.random.normal(135, 30)
        pitch_std        = np.random.normal(12, 5)
        energy_mean      = np.random.normal(0.03, 0.010)
        energy_std       = np.random.normal(0.010, 0.003)
        filler_ratio     = np.random.normal(0.10, 0.03)
        sentiment        = np.random.normal(-0.1, 0.2)
        avg_sent_length  = np.random.normal(8, 3)
        word_count       = np.random.normal(80, 30)
        label            = 0

    return {
        "speaking_rate":   max(40,  min(220, speaking_rate)),
        "pause_ratio":     max(0.0, min(0.9,  pause_ratio)),
        "pitch_mean":      max(80,  min(300,  pitch_mean)),
        "pitch_std":       max(2,   min(80,   pitch_std)),
        "energy_mean":     max(0.001, min(0.15, energy_mean)),
        "energy_std":      max(0.001, min(0.05, energy_std)),
        "filler_ratio":    max(0.0, min(0.3,   filler_ratio)),
        "sentiment":       max(-1,  min(1,     sentiment)),
        "avg_sent_length": max(2,   min(35,    avg_sent_length)),
        "word_count":      max(10,  min(400,   word_count)),
        "label":           label,
    }

# Generate balanced dataset (equal samples per class)
rows = []
for level in [0, 1, 2]:
    for _ in range(NUM_SAMPLES // 3):
        rows.append(generate_sample(level))

df = pd.DataFrame(rows)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save
out_path = os.path.join(os.path.dirname(__file__), "training_data.csv")
df.to_csv(out_path, index=False)
print(f"✅ Generated {len(df)} training samples → {out_path}")
print(df["label"].value_counts().sort_index()
      .rename({0:"Low", 1:"Medium", 2:"High"}))
print("\nFeature preview:")
print(df.drop(columns="label").describe().round(3))