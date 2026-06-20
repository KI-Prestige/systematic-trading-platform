# src/strategy/random_forest_filter.py
# src/strategy/random_forest_filter.py
import pandas as pd
import numpy as np
import ta
from sklearn.ensemble import RandomForestClassifier

class RandomForestFilter:
    def __init__(self):
        self.model = None
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Robust feature creation"""
        features = pd.DataFrame(index=df.index)
        
        # Core features with safe fallbacks
        features['sma_ratio'] = df.get('Close', df.get('equity', 100)) / df.get('short_sma', 100)
        features['adx'] = df.get('adx', 20)
        features['vol_20'] = df.get('vol', 0.02)
        features['volume_ratio'] = df.get('Volume', 1000000) / df.get('avg_vol', 1000000)
        features['weekly_regime'] = (df.get('Close', df.get('equity', 100)) > df.get('weekly_regime_sma', 100)).astype(int)
        
        features['returns'] = df.get('Close', df.get('equity', 100)).pct_change()
        
        # Add RSI and MACD safely
        if 'Close' in df.columns:
            features['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
            features['macd_hist'] = ta.trend.MACD(df['Close']).macd_diff()
        else:
            features['rsi'] = 50
            features['macd_hist'] = 0
        
        for lag in [1, 2, 3, 5]:
            features[f'return_lag_{lag}'] = features['returns'].shift(lag)
        
        return features.fillna(0)
    
    def train(self, df: pd.DataFrame, labels: pd.Series):
        X = self.prepare_features(df)
        self.model = RandomForestClassifier(
            n_estimators=120,
            max_depth=6,
            min_samples_leaf=4,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        )
        self.model.fit(X, labels)
        print(f"✅ RF trained with {X.shape[1]} features on {len(X)} samples")
    
    def get_long_probability(self, df: pd.DataFrame) -> float:
        if self.model is None:
            return 0.5
        X = self.prepare_features(df)
        proba = self.model.predict_proba(X.iloc[[-1]])[:, 1][0]
        return float(proba)