"""Preprocessing utilities for democratic data."""

from typing import Dict, List

import numpy as np

from src.models.voter import Voter


class Preprocessor:
    """Preprocesses data for the democratic decision-making system."""

    def __init__(self) -> None:
        """Initialize the preprocessor."""
        self.feature_means: Dict[str, float] = {}
        self.feature_stds: Dict[str, float] = {}
        self.feature_min: Dict[str, float] = {}
        self.feature_max: Dict[str, float] = {}

    def normalize_preferences(self, voters: List[Voter]) -> List[Voter]:
        """Normalize voter preferences to [0, 1] range.

        Args:
            voters: List of voters

        Returns:
            List of voters with normalized preferences
        """
        all_prefs = []
        for v in voters:
            all_prefs.extend(v.preferences.values())

        if not all_prefs:
            return voters

        min_pref = min(all_prefs)
        max_pref = max(all_prefs)
        range_pref = max_pref - min_pref if max_pref != min_pref else 1.0

        for voter in voters:
            voter.preferences = {
                k: float((v - min_pref) / range_pref) for k, v in voter.preferences.items()
            }

        return voters

    def standardize_preferences(self, voters: List[Voter]) -> List[Voter]:
        """Standardize preferences to zero mean, unit variance.

        Args:
            voters: List of voters

        Returns:
            List of voters with standardized preferences
        """
        all_prefs = []
        for v in voters:
            all_prefs.extend(v.preferences.values())

        if not all_prefs:
            return voters

        mean_pref = np.mean(all_prefs)
        std_pref = np.std(all_prefs) if np.std(all_prefs) != 0 else 1.0

        for voter in voters:
            voter.preferences = {
                k: float((v - mean_pref) / std_pref) for k, v in voter.preferences.items()
            }

        return voters

    def encode_categorical(self, data: List[Dict], categorical_cols: List[str]) -> tuple:
        """Encode categorical features as numeric.

        Args:
            data: List of dictionaries
            categorical_cols: List of categorical column names

        Returns:
            Tuple of (encoded data, mapping dictionaries)
        """
        mappings = {}
        encoded_data = []

        for row in data:
            encoded_row = {}
            for key, value in row.items():
                if key in categorical_cols:
                    if key not in mappings:
                        unique_values = list(set(d[key] for d in data))
                        mappings[key] = {v: i for i, v in enumerate(unique_values)}
                    encoded_row[key] = mappings[key].get(value, 0)
                else:
                    encoded_row[key] = value
            encoded_data.append(encoded_row)

        return encoded_data, mappings
