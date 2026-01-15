#!/usr/bin/env python3
"""
Advanced visualization for ALS-GEDI comparison results
Works standalone - just press Play in PyCharm!

No arguments needed - automatically finds results in standard locations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import os
from pathlib import Path

# ============================================================================
# CONFIGURATION - Edit these paths if your structure is different
# ============================================================================
SUMMARY_CSV = Path(__file__).parent.parent / "results" / "summary_metrics.csv"
GEDI_CSV = "inputs/gedi_table.csv"  # Optional - will work without it
OUTPUT_DIR = Path(__file__).parent.parent / "results/visualization"

# Styling
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10


# ============================================================================


def find_rh_metric_pairs(df):
    """Find all RH metric column pairs (sim/gedi or just available metrics)"""
    pairs = []

    # Look for _sim suffix
    for col in df.columns:
        if col.endswith('_sim'):
            base = col[:-4]
            gedi_col = f"{base}_gedi"
            if gedi_col in df.columns:
                pairs.append((base, col, gedi_col))

    # If no pairs found, look for standalone RH columns
    if not pairs:
        for col in df.columns:
            if col.startswith('RH') and col[2:].replace('_', '').isdigit():
                pairs.append((col, col, None))

    return pairs


def create_als_only_figure(df, output_path):
    """
    Create visualization for ALS-only results (no GEDI comparison)
    Shows distribution of metrics across footprints
    """
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

    # Find RH metrics
    rh_cols = [col for col in df.columns if col.startswith('RH')]

    if not rh_cols:
        print("Warning: No RH metrics found in data")
        return

    # 1. Distribution of RH98 across footprints
    ax1 = fig.add_subplot(gs[0, :2])
    if 'RH98' in df.columns:
        data = df['RH98'].dropna()
        ax1.hist(data, bins=30, color='#3b82f6', alpha=0.7, edgecolor='black')
        ax1.axvline(data.mean(), color='red', linestyle='--', linewidth=2,
                    label=f'Mean = {data.mean():.2f} m')
        ax1.axvline(data.median(), color='green', linestyle='--', linewidth=2,
                    label=f'Median = {data.median():.2f} m')
        ax1.set_xlabel('Canopy Height RH98 (m)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Number of Footprints', fontsize=12, fontweight='bold')
        ax1.set_title('Distribution of Canopy Heights (RH98)', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')

        # Add statistics box
        stats_text = f'n = {len(data)}\nMean = {data.mean():.2f} m\n'
        stats_text += f'Std = {data.std():.2f} m\nMin = {data.min():.2f} m\n'
        stats_text += f'Max = {data.max():.2f} m'
        ax1.text(0.98, 0.97, stats_text, transform=ax1.transAxes,
                 fontsize=9, verticalalignment='top', horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # 2. Summary statistics for all RH metrics
    ax2 = fig.add_subplot(gs[0, 2])
    stats_data = []
    for col in sorted(rh_cols):
        if col in df.columns:
            data = df[col].dropna()
            if len(data) > 0:
                stats_data.append({
                    'metric': col,
                    'mean': data.mean(),
                    'std': data.std()
                })

    if stats_data:
        stats_df = pd.DataFrame(stats_data)
        ax2.barh(stats_df['metric'], stats_df['mean'], color='#10b981', alpha=0.7)
        ax2.set_xlabel('Mean Height (m)', fontsize=10, fontweight='bold')
        ax2.set_title('Mean RH Metrics', fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')

    # 3-6. Distributions for other RH metrics
    positions = [(1, 0), (1, 1), (1, 2), (2, 0)]
    metrics_to_plot = ['RH50', 'RH75', 'RH90', 'RH25']

    for pos, metric in zip(positions, metrics_to_plot):
        if metric in df.columns:
            ax = fig.add_subplot(gs[pos[0], pos[1]])
            data = df[metric].dropna()

            if len(data) > 0:
                ax.hist(data, bins=20, color='#8b5cf6', alpha=0.7, edgecolor='black')
                ax.axvline(data.mean(), color='red', linestyle='--', linewidth=1.5)

                ax.text(0.97, 0.97,
                        f'Mean: {data.mean():.1f}m\nStd: {data.std():.1f}m',
                        transform=ax.transAxes, fontsize=9,
                        verticalalignment='top', horizontalalignment='right',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

                ax.set_xlabel(f'{metric} Height (m)', fontsize=9)
                ax.set_ylabel('Count', fontsize=9)
                ax.set_title(f'{metric} Distribution', fontsize=10, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='y')

    # 7. Vertical profile shape (if FHD available)
    ax7 = fig.add_subplot(gs[2, 1:])
    if 'FHD' in df.columns:
        data = df['FHD'].dropna()
        if len(data) > 0:
            ax7.hist(data, bins=25, color='#f59e0b', alpha=0.7, edgecolor='black')
            ax7.axvline(data.mean(), color='red', linestyle='--', linewidth=2,
                        label=f'Mean = {data.mean():.3f}')
            ax7.set_xlabel('Foliage Height Diversity (FHD)', fontsize=11, fontweight='bold')
            ax7.set_ylabel('Number of Footprints', fontsize=11, fontweight='bold')
            ax7.set_title('Vertical Complexity Distribution', fontsize=12, fontweight='bold')
            ax7.legend()
            ax7.grid(True, alpha=0.3, axis='y')
    else:
        # Show RH range instead
        if all(m in df.columns for m in ['RH25', 'RH75']):
            df['rh_range'] = df['RH75'] - df['RH25']
            data = df['rh_range'].dropna()
            if len(data) > 0:
                ax7.hist(data, bins=25, color='#f59e0b', alpha=0.7, edgecolor='black')
                ax7.axvline(data.mean(), color='red', linestyle='--', linewidth=2)
                ax7.set_xlabel('RH Range (RH75 - RH25) [m]', fontsize=11, fontweight='bold')
                ax7.set_ylabel('Count', fontsize=11, fontweight='bold')
                ax7.set_title('Canopy Thickness Distribution', fontsize=12, fontweight='bold')
                ax7.grid(True, alpha=0.3, axis='y')

    plt.suptitle('ALS Vertical Structure Analysis',
                 fontsize=16, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def create_comparison_figure(df, output_path):
    """Create comprehensive comparison figure when both ALS and GEDI data available"""
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)

    pairs = find_rh_metric_pairs(df)

    # 1. Main scatter plot (RH98)
    ax1 = fig.add_subplot(gs[0, :2])
    rh98_pair = next((p for p in pairs if p[0] == 'RH98'), None)

    if rh98_pair:
        _, sim_col, gedi_col = rh98_pair
        x = df[gedi_col].dropna()
        y = df[sim_col].dropna()
        common_idx = x.index.intersection(y.index)
        x = x[common_idx]
        y = y[common_idx]

        if len(x) > 0:
            ax1.scatter(x, y, alpha=0.6, s=50, c='#3b82f6',
                        edgecolors='white', linewidth=0.5)

            min_val = min(x.min(), y.min())
            max_val = max(x.max(), y.max())
            ax1.plot([min_val, max_val], [min_val, max_val],
                     'r--', linewidth=2, label='1:1 line')

            bias = np.mean(y - x)
            rmse = np.sqrt(np.mean((y - x) ** 2))
            r2 = np.corrcoef(x, y)[0, 1] ** 2 if len(x) > 1 else 0

            stats_text = f'n = {len(x)}\n'
            stats_text += f'Bias = {bias:.2f} m\n'
            stats_text += f'RMSE = {rmse:.2f} m\n'
            stats_text += f'R2 = {r2:.3f}'

            ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes,
                     fontsize=10, verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    ax1.set_xlabel('GEDI RH98 (m)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('ALS RH98 (m)', fontsize=12, fontweight='bold')
    ax1.set_title('Canopy Height Comparison (RH98)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # 2. RMSE summary
    ax2 = fig.add_subplot(gs[0, 2])
    stats_data = []

    for base, sim_col, gedi_col in pairs:
        if gedi_col:
            x = df[gedi_col].dropna()
            y = df[sim_col].dropna()
            common_idx = x.index.intersection(y.index)

            if len(common_idx) > 0:
                x = x[common_idx]
                y = y[common_idx]
                rmse = np.sqrt(np.mean((y - x) ** 2))
                stats_data.append({'metric': base, 'rmse': rmse})

    if stats_data:
        stats_df = pd.DataFrame(stats_data)
        ax2.barh(stats_df['metric'], stats_df['rmse'], color='#10b981')
        ax2.set_xlabel('RMSE (m)', fontsize=10)
        ax2.set_title('RMSE by Metric', fontsize=11, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')

    # 3-6. Additional scatter plots
    positions = [(1, 0), (1, 1), (1, 2), (2, 0)]
    metrics_to_plot = ['RH50', 'RH75', 'RH90', 'RH25']

    for pos, metric in zip(positions, metrics_to_plot):
        pair = next((p for p in pairs if p[0] == metric), None)
        if pair:
            ax = fig.add_subplot(gs[pos[0], pos[1]])
            _, sim_col, gedi_col = pair

            x = df[gedi_col].dropna()
            y = df[sim_col].dropna()
            common_idx = x.index.intersection(y.index)

            if len(common_idx) > 0:
                x = x[common_idx]
                y = y[common_idx]

                ax.scatter(x, y, alpha=0.5, s=30, c='#8b5cf6')

                min_val = min(x.min(), y.min())
                max_val = max(x.max(), y.max())
                ax.plot([min_val, max_val], [min_val, max_val],
                        'r--', linewidth=1.5)

                r2 = np.corrcoef(x, y)[0, 1] ** 2 if len(x) > 1 else 0
                ax.text(0.05, 0.95, f'R2 = {r2:.2f}',
                        transform=ax.transAxes, verticalalignment='top',
                        fontsize=9,
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

                ax.set_xlabel(f'GEDI {metric} (m)', fontsize=9)
                ax.set_ylabel(f'ALS {metric} (m)', fontsize=9)
                ax.set_title(metric, fontsize=10, fontweight='bold')
                ax.grid(True, alpha=0.3)

    # 7. Error distribution
    ax7 = fig.add_subplot(gs[2, 1:])
    if rh98_pair:
        _, sim_col, gedi_col = rh98_pair
        x = df[gedi_col].dropna()
        y = df[sim_col].dropna()
        common_idx = x.index.intersection(y.index)
        errors = (y[common_idx] - x[common_idx]).values

        if len(errors) > 0:
            ax7.hist(errors, bins=30, color='#3b82f6', alpha=0.7, edgecolor='black')
            ax7.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero')
            ax7.axvline(np.mean(errors), color='green', linestyle='-',
                        linewidth=2, label=f'Bias = {np.mean(errors):.2f} m')
            ax7.set_xlabel('Error (ALS - GEDI) [m]', fontsize=11, fontweight='bold')
            ax7.set_ylabel('Frequency', fontsize=11, fontweight='bold')
            ax7.set_title('Error Distribution RH98', fontsize=12, fontweight='bold')
            ax7.legend()
            ax7.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Comprehensive ALS-GEDI Comparison',
                 fontsize=16, fontweight='bold', y=0.98)

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def create_profile_example(output_path):
    """Create example vertical profile visualization"""
    z = np.arange(0, 40, 0.5)

    # Simulate ALS profile
    als_profile = (np.exp(-0.5 * ((z - 20) / 5) ** 2) * 1.2 +
                   np.exp(-0.5 * ((z - 5) / 2) ** 2) * 0.3)

    # Simulate GEDI profile (slightly smoothed)
    gedi_profile = (np.exp(-0.5 * ((z - 19.5) / 5.2) ** 2) * 1.15 +
                    np.exp(-0.5 * ((z - 4.8) / 2.1) ** 2) * 0.28)

    fig, ax = plt.subplots(figsize=(8, 10))

    ax.plot(als_profile, z, linewidth=2, color='#3b82f6', label='ALS profile')
    ax.plot(gedi_profile, z, linewidth=2, color='#10b981',
            linestyle='--', label='GEDI profile')

    ax.set_ylabel('Height (m)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Energy / Density', fontsize=14, fontweight='bold')
    ax.set_title('Vertical Profile Comparison\n(Example Footprint)',
                 fontsize=15, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    # Mark RH levels
    cum_als = np.cumsum(als_profile)
    cum_als /= cum_als[-1]

    for p in [25, 50, 75, 98]:
        rh = np.interp(p / 100, cum_als, z)
        ax.axhline(rh, color='gray', linestyle=':', alpha=0.5)
        ax.text(max(als_profile.max(), gedi_profile.max()) * 0.85, rh,
                f'RH{p}', fontsize=9, va='center')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def create_quality_summary(df, has_gedi, output_path):
    """Create quality and parameter summary"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 1. Footprint counts
    ax = axes[0, 0]
    rh_cols = [col for col in df.columns if 'RH' in col]
    counts = []
    labels = []

    for col in sorted(rh_cols):
        if col in df.columns:
            count = df[col].notna().sum()
            if count > 0:
                counts.append(count)
                # Clean up label
                label = col.replace('_sim', '').replace('_gedi', '')
                if label not in labels:
                    labels.append(label)
                    counts[-1] = count
                else:
                    counts.pop()

    if counts and len(counts) == len(labels):
        ax.bar(labels, counts, color='#3b82f6', alpha=0.7)
        ax.set_ylabel('Count', fontsize=11, fontweight='bold')
        ax.set_title('Valid Footprints by Metric', fontsize=12, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3, axis='y')

    # 2. R2 or Standard Deviation
    ax = axes[0, 1]

    if has_gedi:
        # Show R2 if GEDI available
        pairs = find_rh_metric_pairs(df)
        r2_values = []
        r2_labels = []

        for base, sim_col, gedi_col in pairs:
            if gedi_col:
                x = df[gedi_col].dropna()
                y = df[sim_col].dropna()
                common_idx = x.index.intersection(y.index)
                if len(common_idx) > 1:
                    r2 = np.corrcoef(x[common_idx], y[common_idx])[0, 1] ** 2
                    r2_values.append(r2)
                    r2_labels.append(base)

        if r2_values:
            colors = ['#10b981' if r2 > 0.75 else '#f59e0b' for r2 in r2_values]
            ax.bar(r2_labels, r2_values, color=colors, alpha=0.7)
            ax.axhline(0.75, color='red', linestyle='--',
                       linewidth=2, label='Quality threshold')
            ax.set_ylabel('R2', fontsize=11, fontweight='bold')
            ax.set_title('Coefficient of Determination', fontsize=12, fontweight='bold')
            ax.set_ylim([0, 1])
            ax.tick_params(axis='x', rotation=45)
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
    else:
        # Show standard deviation
        std_values = []
        std_labels = []

        for col in sorted(rh_cols):
            if col in df.columns:
                data = df[col].dropna()
                if len(data) > 0:
                    label = col.replace('_sim', '')
                    if label not in std_labels:
                        std_values.append(data.std())
                        std_labels.append(label)

        if std_values:
            ax.bar(std_labels, std_values, color='#8b5cf6', alpha=0.7)
            ax.set_ylabel('Standard Deviation (m)', fontsize=11, fontweight='bold')
            ax.set_title('Variability Across Footprints', fontsize=12, fontweight='bold')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3, axis='y')

    # 3. Text summary
    ax = axes[1, 0]
    ax.axis('off')

    summary_text = f"DATA QUALITY SUMMARY\n\n"
    summary_text += f"Total footprints: {len(df)}\n\n"

    if has_gedi and 'RH98_sim' in df.columns and 'RH98_gedi' in df.columns:
        x = df['RH98_gedi'].dropna()
        y = df['RH98_sim'].dropna()
        common_idx = x.index.intersection(y.index)

        if len(common_idx) > 0:
            x = x[common_idx]
            y = y[common_idx]
            bias = np.mean(y - x)
            rmse = np.sqrt(np.mean((y - x) ** 2))
            r2 = np.corrcoef(x, y)[0, 1] ** 2

            summary_text += f"Average statistics (RH98):\n"
            summary_text += f"  Bias: {bias:.2f} m\n"
            summary_text += f"  RMSE: {rmse:.2f} m\n"
            summary_text += f"  R2: {r2:.3f}\n\n"
            summary_text += "Quality assessment:\n"

            if abs(bias) < 1.5 and rmse < 5 and r2 > 0.7:
                summary_text += "  GOOD (publishable)"
                color = 'lightgreen'
            elif abs(bias) < 2.5 and rmse < 7 and r2 > 0.6:
                summary_text += "  FAIR (needs discussion)"
                color = 'lightyellow'
            else:
                summary_text += "  NEEDS IMPROVEMENT"
                color = 'lightcoral'
    else:
        if 'RH98' in df.columns:
            data = df['RH98'].dropna()
            summary_text += f"RH98 statistics:\n"
            summary_text += f"  Mean: {data.mean():.2f} m\n"
            summary_text += f"  Std: {data.std():.2f} m\n"
            summary_text += f"  Min: {data.min():.2f} m\n"
            summary_text += f"  Max: {data.max():.2f} m\n"
        color = 'lightblue'

    ax.text(0.1, 0.5, summary_text, fontsize=10, verticalalignment='center',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))

    # 4. Pipeline parameters
    ax = axes[1, 1]
    ax.axis('off')

    params_text = """PIPELINE PARAMETERS

Footprint:
  Gaussian sigma: 5.5 m
  Radius: 15.0 m

Vertical resolution:
  Profile: 0.5 m
  Waveform: 0.15 m

Physical model:
  k (attenuation): 0.028
  sigma (pulse): 0.6 m
  SNR: 30 dB

GEDI quality filters:
  Sensitivity >= 0.95
  Degrade flag = 0
  Slope <= 15 deg
"""

    ax.text(0.1, 0.5, params_text, fontsize=9, verticalalignment='center',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    title = 'Quality and Parameters Summary'
    if not has_gedi:
        title += ' (ALS only)'

    plt.suptitle(title, fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def main():
    """
    Main function - no arguments needed!
    Automatically detects available data and creates appropriate visualizations.
    """
    print("=" * 70)
    print("ALS-GEDI Advanced Visualization")
    print("=" * 70)

    # Check if summary file exists
    if not os.path.exists(SUMMARY_CSV):
        print(f"\nERROR: Summary file not found: {SUMMARY_CSV}")
        print("\nPlease run the pipeline first:")
        print("  python auto_run.py")
        print("  OR")
        print("  python pipeline_batch.py --footprints inputs/footprints.csv --las inputs/als/file.laz")
        return

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\nOutput directory: {OUTPUT_DIR}/")

    # Load data
    print(f"\nLoading data from: {SUMMARY_CSV}")
    df_sim = pd.read_csv(SUMMARY_CSV)
    print(f"  Loaded {len(df_sim)} footprints")

    # Check for GEDI data
    has_gedi = False
    if os.path.exists(GEDI_CSV):
        print(f"\nGEDI data found: {GEDI_CSV}")
        df_gedi = pd.read_csv(GEDI_CSV)

        if 'footprint_id' in df_gedi.columns and 'footprint_id' in df_sim.columns:
            print("  Merging ALS and GEDI data...")
            df = pd.merge(df_sim, df_gedi, on='footprint_id',
                          how='inner', suffixes=('_sim', '_gedi'))
            print(f"  Matched {len(df)} footprints")
            has_gedi = True
        else:
            print("  Warning: Cannot merge - missing footprint_id column")
            df = df_sim
    else:
        print(f"\nNo GEDI data found at: {GEDI_CSV}")
        print("  Creating ALS-only visualizations")
        df = df_sim

    # Create visualizations
    print("\n" + "=" * 70)
    print("Creating visualizations...")
    print("=" * 70)

    if has_gedi:
        print("\n[1/3] Creating comprehensive comparison figure...")
        create_comparison_figure(df, os.path.join(OUTPUT_DIR, 'comprehensive_analysis.png'))
    else:
        print("\n[1/3] Creating ALS-only analysis figure...")
        create_als_only_figure(df, os.path.join(OUTPUT_DIR, 'comprehensive_analysis.png'))

    print("\n[2/3] Creating profile comparison...")
    create_profile_example(os.path.join(OUTPUT_DIR, 'profile_comparison.png'))

    print("\n[3/3] Creating quality summary...")
    create_quality_summary(df, has_gedi, os.path.join(OUTPUT_DIR, 'quality_summary.png'))

    # Summary
    print("\n" + "=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    print(f"\nGenerated files in {OUTPUT_DIR}/:")
    print("  1. comprehensive_analysis.png - Main analysis")
    print("  2. profile_comparison.png    - Vertical profiles")
    print("  3. quality_summary.png        - Quality and parameters")
    print("\nYou can open these files directly or view them in your file browser.")
    print("=" * 70)


if __name__ == "__main__":
    # Just run - no arguments needed!
    main()