import os
import os.path as op
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

if os.name == "nt":
    _libs_path = op.join(op.dirname(op.dirname(op.dirname(__file__))), "Lib", "site-packages", "sklearn", ".libs")
    if op.isdir(_libs_path) and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(_libs_path)
        except Exception:
            pass

import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split

from backend.engines.flood_engine import FloodEngine
from backend.models.flood_models import FloodRiskLevel
from backend.models.ml_models import MLModelStatus


class MLEngine:
    """Trains and executes RandomForest regression and classification models to complement physics-based flood intelligence."""

    FEATURE_NAMES: List[str] = [
        "rainfall_intensity_mm_hr",
        "forecast_peak_rainfall_mm_hr",
        "elevation_m",
        "slope_percent",
        "flow_accumulation",
        "imperviousness",
        "runoff_coefficient_c",
        "runoff_discharge_m3_s",
        "is_low_lying",
        "drainage_capacity_m3s",
        "drainage_effective_capacity_m3s",
        "drainage_utilization_percent",
        "blockage_percent",
        "excess_flow_m3s",
        "physics_flood_depth_cm",
    ]

    def __init__(self, random_state: int = 42, auto_train: bool = False):
        self.random_state = random_state
        self.regressor: Optional[RandomForestRegressor] = None
        self.classifier: Optional[RandomForestClassifier] = None
        self.training_samples_count: int = 0
        self.validation_metrics: Dict[str, float] = {}
        self.trained_at: Optional[str] = None
        self._is_trained: bool = False

        if auto_train:
            self.train_models()

    def generate_synthetic_training_data(
        self, num_samples: int = 600
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generates synthetic training dataset covering diverse urban storm and drainage regimes.
        Explicitly labeled: SYNTHETIC ML TRAINING DATA.
        """
        rng = np.random.RandomState(self.random_state)

        rainfall = rng.uniform(0.0, 150.0, size=num_samples)
        # Ensure 10% zero rainfall baseline samples
        zero_indices = rng.choice(num_samples, size=int(num_samples * 0.10), replace=False)
        rainfall[zero_indices] = 0.0

        forecast_peak = rainfall * rng.uniform(1.0, 1.25, size=num_samples)
        elevation = rng.uniform(10.0, 45.0, size=num_samples)
        slope = rng.uniform(0.3, 8.0, size=num_samples)
        flow_accumulation = rng.uniform(100.0, 3000.0, size=num_samples)
        imperviousness = rng.uniform(0.15, 0.95, size=num_samples)

        runoff_c = 0.15 + (0.75 * imperviousness) + (0.05 * np.minimum(1.0, slope / 5.0))
        runoff_c = np.clip(runoff_c, 0.15, 0.98)
        runoff_q = (runoff_c * rainfall * rng.uniform(2.5, 6.0, size=num_samples)) / 360.0

        is_low_lying = np.where((elevation < 16.0) & (slope < 1.5), 1.0, 0.0)

        drain_cap = rng.uniform(2.0, 7.0, size=num_samples)
        blockage = rng.uniform(0.0, 60.0, size=num_samples)
        eff_cap = drain_cap * (1.0 - (blockage / 100.0))

        # Conduit flow includes local runoff plus upstream network inflows scaled with rainfall
        upstream_inflow = rng.uniform(0.5, 4.5, size=num_samples) * (rainfall / 70.0)
        flow = np.maximum(0.0, runoff_q + upstream_inflow)
        utilization = np.where(eff_cap > 0, (flow / np.maximum(0.1, eff_cap)) * 100.0, 999.9)
        excess_flow = np.maximum(0.0, flow - eff_cap)

        # Baseline physics depth calculation aligned with FloodEngine
        flood_prone_index = (
            0.35 * np.clip((40.0 - elevation) / 30.0, 0.0, 1.0)
            + 0.25 * np.clip(1.0 - (slope / 4.0), 0.0, 1.0)
            + 0.25 * np.clip(flow_accumulation / 2500.0, 0.0, 1.0)
            + 0.15 * imperviousness
        )
        flood_prone_index = np.where(is_low_lying == 1.0, np.maximum(flood_prone_index, 0.55), flood_prone_index)

        d_runoff = 14.0 * flood_prone_index * (rainfall / 100.0)
        d_surcharge = 10.0 * excess_flow * (1.0 + (flow_accumulation / 2500.0))
        d_backpressure = np.where(
            utilization > 70.0,
            6.0 * np.minimum(1.0, (utilization - 70.0) / 30.0) * flood_prone_index,
            0.0,
        )
        blockage_factor = 1.0 + (blockage / 200.0)
        physics_depth = (d_runoff + d_surcharge + d_backpressure) * blockage_factor
        physics_depth = np.where(rainfall <= 0.0, 0.0, np.maximum(0.0, physics_depth))

        # Target flood depth: physics ground truth + subtle empirical non-linearities and noise
        noise = rng.normal(0.0, 0.8, size=num_samples)
        target_depth = np.where(
            rainfall <= 0.0,
            0.0,
            np.maximum(0.0, (physics_depth * rng.uniform(0.96, 1.04, size=num_samples)) + noise),
        )

        # Binary hazard classification (1 = hazardous ponding >= 15 cm, 0 = safe / minor)
        target_hazard = np.where(target_depth >= 15.0, 1, 0)

        # Build feature matrix matching exact FEATURE_NAMES order
        X = np.column_stack([
            rainfall,
            forecast_peak,
            elevation,
            slope,
            flow_accumulation,
            imperviousness,
            runoff_c,
            runoff_q,
            is_low_lying,
            drain_cap,
            eff_cap,
            utilization,
            blockage,
            excess_flow,
            physics_depth,
        ])

        return X, target_depth, target_hazard

    def train_models(self, force_retrain: bool = False) -> None:
        """Trains the regression and classification tree ensembles on synthetic simulation curves."""
        if self._is_trained and not force_retrain:
            return

        X, y_depth, y_hazard = self.generate_synthetic_training_data(num_samples=600)
        self.training_samples_count = len(X)

        X_train, X_val, y_train_depth, y_val_depth, y_train_haz, y_val_haz = train_test_split(
            X, y_depth, y_hazard, test_size=0.20, random_state=self.random_state
        )

        # 1. Depth Regressor (RandomForest)
        reg = RandomForestRegressor(
            n_estimators=50,
            max_depth=8,
            random_state=self.random_state,
            n_jobs=1
        )
        reg.fit(X_train, y_train_depth)
        self.regressor = reg

        # 2. Hazard Classifier (RandomForest)
        clf = RandomForestClassifier(
            n_estimators=50,
            max_depth=8,
            random_state=self.random_state,
            n_jobs=1
        )
        clf.fit(X_train, y_train_haz)
        self.classifier = clf

        # 3. Validation Metrics on 20% holdout split
        val_pred_depth = reg.predict(X_val)
        val_pred_haz = clf.predict(X_val)

        mae = float(mean_absolute_error(y_val_depth, val_pred_depth))
        rmse = float(np.sqrt(mean_squared_error(y_val_depth, val_pred_depth)))
        r2 = float(r2_score(y_val_depth, val_pred_depth))
        acc = float(accuracy_score(y_val_haz, val_pred_haz))
        f1 = float(f1_score(y_val_haz, val_pred_haz, average="weighted"))

        self.validation_metrics = {
            "mae": round(mae, 3),
            "rmse": round(rmse, 3),
            "r2_score": round(r2, 3),
            "classification_accuracy": round(acc, 3),
            "f1_score": round(f1, 3),
        }

        self.trained_at = datetime.now(timezone.utc).isoformat()
        self._is_trained = True

    def extract_feature_vector(self, feature_dict: Dict[str, Any]) -> List[float]:
        """Extracts ordered feature vector matching FEATURE_NAMES specification."""
        vector = []
        for name in self.FEATURE_NAMES:
            val = float(feature_dict.get(name, 0.0))
            vector.append(val)
        return vector

    def predict_zone(
        self, feature_dict: Dict[str, Any]
    ) -> Tuple[float, FloodRiskLevel, float, float]:
        """
        Executes ML inference for a single zone.
        Returns: (predicted_depth_cm, predicted_risk_level, flood_probability, model_confidence)
        """
        if not self._is_trained:
            self.train_models()

        vector = self.extract_feature_vector(feature_dict)
        X_in = np.array([vector])

        # Guard: Zero rainfall must always result in zero surface flood depth
        if feature_dict.get("rainfall_intensity_mm_hr", 0.0) <= 0.0:
            return 0.0, FloodRiskLevel.LOW, 0.0, 0.95

        # 1. Flood depth regression
        raw_depth = float(self.regressor.predict(X_in)[0])
        pred_depth = round(max(0.0, raw_depth), 1)

        # 2. Risk classification (reusing centralized Phase 5 thresholds)
        risk_level = FloodEngine.classify_flood_risk(pred_depth)

        # 3. Hazard probability (depth >= 15 cm) from classifier
        if hasattr(self.classifier, "predict_proba"):
            probs = self.classifier.predict_proba(X_in)[0]
            # Probability of class 1 (hazard)
            classes = list(self.classifier.classes_)
            if 1 in classes:
                haz_idx = classes.index(1)
                prob = float(probs[haz_idx])
            else:
                prob = 0.0 if pred_depth < 15.0 else 0.9
        else:
            prob = min(1.0, pred_depth / 30.0)
        prob = round(max(0.0, min(1.0, prob)), 2)

        # 4. Model confidence from tree ensemble variance
        # Lower tree variance indicates higher ensemble consensus
        tree_preds = [float(tree.predict(X_in)[0]) for tree in self.regressor.estimators_]
        std_err = float(np.std(tree_preds))
        confidence = max(0.65, min(0.95, 1.0 - (std_err / max(10.0, pred_depth + 5.0))))
        confidence = round(confidence, 2)

        return pred_depth, risk_level, prob, confidence

    def get_status(self) -> MLModelStatus:
        """Returns metadata, feature list, and synthetic validation metrics."""
        if not self._is_trained:
            self.train_models()

        return MLModelStatus(
            model_loaded=self._is_trained,
            model_type="RandomForestRegressor + RandomForestClassifier (scikit-learn)",
            training_samples=self.training_samples_count,
            features=self.FEATURE_NAMES,
            validation_metrics=self.validation_metrics,
            trained_at=self.trained_at or datetime.now(timezone.utc).isoformat(),
            data_provenance="SYNTHETIC ML TRAINING DATA",
            disclaimer="Trained on synthetic hydrological simulation curves for prototype demonstration. Does not reflect real-world physical validation."
        )


# Global singleton instance
default_ml_engine = MLEngine()
