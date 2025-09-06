"""
Utilities for sharing data between notebook segments
"""

import pandas as pd
import pickle
import os
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path


class ProjectConfig:
    """Centralized configuration for the project"""

    def __init__(self):
        self.data_dir = Path("data/")
        self.output_dir = Path("outputs/")
        self.figures_dir = Path("figures/")
        self.models_dir = Path("models/")

        # Create directories if they don't exist
        for dir_path in [
            self.data_dir,
            self.output_dir,
            self.figures_dir,
            self.models_dir,
        ]:
            dir_path.mkdir(exist_ok=True)


def save_intermediate_results(data, filename, config):
    """Save intermediate results between notebooks"""
    filepath = config.output_dir / filename

    if isinstance(data, pd.DataFrame):
        data.to_pickle(filepath)
    else:
        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    print(f"Saved: {filepath}")
    return filepath


def load_intermediate_results(filename, config):
    """Load results from previous notebook"""
    filepath = config.output_dir / filename

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if filename.endswith(".pkl"):
        if "df" in filename.lower() or "data" in filename.lower():
            return pd.read_pickle(filepath)
        else:
            with open(filepath, "rb") as f:
                return pickle.load(f)


def list_available_results(config):
    """List all available intermediate results"""
    files = list(config.output_dir.glob("*.pkl"))
    if files:
        print("Available intermediate results:")
        for f in files:
            print(f"  - {f.name}")
    else:
        print("No intermediate results found")
    return files


def save_project_figure(filename, title, config):
    plt.title(title)
    filepath = os.path.join(config.figures_dir, f"{filename}.png")
    plt.savefig(
        filepath, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
    )
    print(f"Saved: {filepath}")
    return filepath


def reset_plot_settings():
    """Reset both matplotlib and seaborn to clean defaults"""
    plt.close("all")  # Close existing figures
    plt.rcdefaults()  # Reset matplotlib
    sns.reset_defaults()  # Reset seaborn
