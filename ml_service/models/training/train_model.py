import numpy as np
import pandas as pd
import joblib
import os
from sklearn.ensemble           import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection    import train_test_split, cross_val_score
from sklearn.preprocessing      import StandardScaler
from sklearn.pipeline           import Pipeline
from sklearn.metrics            import classification_report, mean_absolute_error

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_PATH   = os.path.join(BASE_DIR, "training_data.csv")
MODELS_DIR  = os.path.join(BASE_DIR, "..", "models")
MODELS_DIR  = os.path.abspath(MODELS_DIR)  # resolve any .. in path
os.makedirs(MODELS_DIR, exist_ok=True)
print(f"📁 Models will be saved to: {MODELS_DIR}")

FEATURES = [
    "speaking_rate", "pause_ratio", "pitch_mean", "pitch_std",
    "energy_mean",   "energy_std",  "filler_ratio", "sentiment",
    "avg_sent_length", "word_count",
]

# ── Load Data ──────────────────────────────────────────────────
print("📂 Loading training data...")
df = pd.read_csv(DATA_PATH)
X  = df[FEATURES]
y_class = df["label"]   # 0=Low, 1=Medium, 2=High

# Create a continuous score (0–100) for regression
# High=75–100, Medium=45–70, Low=10–40
def label_to_score(row):
    base = {2: 82, 1: 57, 0: 25}[row["label"]]
    noise = np.random.normal(0, 7)
    return max(0, min(100, base + noise))

np.random.seed(42)
y_score = df.apply(label_to_score, axis=1)

X_train, X_test, yc_train, yc_test, ys_train, ys_test = train_test_split(
    X, y_class, y_score, test_size=0.2, random_state=42, stratify=y_class
)

# ── 1. Confidence Classifier (Random Forest) ──────────────────
print("\n🌲 Training confidence classifier (Random Forest)...")
clf_pipeline = Pipeline([
    ("scaler",     StandardScaler()),
    ("classifier", RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )),
])
clf_pipeline.fit(X_train, yc_train)

# Cross-validation
cv_scores = cross_val_score(clf_pipeline, X_train, yc_train, cv=5, scoring="accuracy")
print(f"   CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# Test set
y_pred_class = clf_pipeline.predict(X_test)
print("\n📊 Classification Report:")
print(classification_report(
    yc_test, y_pred_class,
    target_names=["Low", "Medium", "High"]
))

# Feature importances
importances = clf_pipeline.named_steps["classifier"].feature_importances_
feat_imp = sorted(zip(FEATURES, importances), key=lambda x: -x[1])
print("🔑 Feature importances:")
for feat, imp in feat_imp:
    bar = "█" * int(imp * 50)
    print(f"   {feat:<20} {bar} {imp:.3f}")

# ── 2. Confidence Score Regressor (Gradient Boosting) ─────────
print("\n📈 Training confidence score regressor (GradientBoosting)...")
reg_pipeline = Pipeline([
    ("scaler",     StandardScaler()),
    ("regressor",  GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
    )),
])
reg_pipeline.fit(X_train, ys_train)

y_pred_score = reg_pipeline.predict(X_test)
mae = mean_absolute_error(ys_test, y_pred_score)
print(f"   Mean Absolute Error: {mae:.2f} points")

cv_reg = cross_val_score(
    reg_pipeline, X_train, ys_train, cv=5, scoring="neg_mean_absolute_error"
)
print(f"   CV MAE: {-cv_reg.mean():.2f} ± {cv_reg.std():.2f}")

# ── Save Models ────────────────────────────────────────────────
clf_path = os.path.join(MODELS_DIR, "confidence_classifier.pkl")
reg_path = os.path.join(MODELS_DIR, "confidence_regressor.pkl")

joblib.dump(clf_pipeline, clf_path)
joblib.dump(reg_pipeline, reg_path)

print(f"\n✅ Saved classifier  → {clf_path}")
print(f"✅ Saved regressor   → {reg_path}")
print("\n🎉 Training complete! Run app.py to start the ML server.")