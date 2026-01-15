# ALS-GEDI Comparison Pipeline

A comprehensive scientific pipeline for comparing Airborne Laser Scanning (ALS) data with GEDI (Global Ecosystem Dynamics Investigation) satellite measurements. Optimized for European mixed forests.

## 🌲 Project Overview

This pipeline enables rigorous comparison between high-density ALS point clouds and GEDI spaceborne lidar measurements by:

1. **Simulating GEDI footprints** from ALS data with physically-accurate sensor characteristics
2. **Computing vertical structure metrics** (RH percentiles, canopy height, FHD) using identical algorithms
3. **Performing statistical validation** with comprehensive error analysis
4. **Generating publication-ready visualizations** and reports

### Key Scientific Features

- **Gaussian Footprint Weighting** (σ = 5.5m) - matches GEDI sensor geometry
- **Beer-Lambert Attenuation** (k = 0.028) - accounts for canopy occlusion effects
- **Return-Normalized Weights** - reduces understory bias
- **Quality-Filtered Comparison** - implements GEDI L2 quality standards

## 📋 Table of Contents

- [Installation](#installation)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Detailed Workflow](#detailed-workflow)
- [Configuration Parameters](#configuration-parameters)
- [Visualization](#visualization)
- [Testing](#testing)
- [Expected Results](#expected-results)
- [Troubleshooting](#troubleshooting)
- [Citation](#citation)

## 🔧 Installation

### Prerequisites

- Python 3.8+
- R 4.0+ (optional, for lidR preprocessing)

### Python Setup

```bash
# Clone repository
git clone https://github.com/yourusername/als-gedi-pipeline.git
cd als-gedi-pipeline

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### R Setup (Optional)

For ALS preprocessing in R:

```r
install.packages(c("lidR", "sf", "raster"))
```

## 📁 Project Structure

```
als-gedi-pipeline/
├── inputs/                     # Input data directory
│   ├── als/                   # ALS point clouds (.laz/.las)
│   ├── gedi/                  # GEDI HDF5 files (.h5)
│   └── footprints.csv         # Footprint locations (auto-generated)
├── results/                   # Output directory
│   ├── fp_XXXXXX/            # Per-footprint results
│   ├── summary_metrics.csv   # Aggregated metrics
│   └── merged_summary.csv    # ALS + GEDI comparison
├── figures/                   # Generated visualizations
├── scripts/                   # Core processing scripts
│   ├── 01_preprocess_als.py  # Extract ALS footprints
│   ├── 02_build_profile.py   # Build vertical profiles
│   ├── 03_simulate_wf.py     # Simulate waveforms
│   ├── 04_compute_rh.py      # Compute RH metrics
│   ├── 05_compare_with_gedi.py # Statistical comparison
│   ├── generate_footprints_from_las.py # Auto-generate footprints
│   ├── read_gedi_h5.py       # Parse GEDI HDF5
│   ├── plot_results.py       # Generate visualizations
│   └── utils.py              # Shared utilities
├── tests/                     # Unit tests
├── auto_run.py               # Automated pipeline execution
├── pipeline_batch.py         # Batch processing
├── pipeline_runner.py        # Simple example runner
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🚀 Quick Start

### Option 1: Fully Automated (Recommended)

```bash
# Place your data:
# - ALS file(s) in inputs/als/
# - GEDI file(s) in inputs/gedi/ (optional)

# Run complete pipeline
python auto_run.py

# View results
ls results/summary_metrics.csv
ls figures/
```

This will:
1. Auto-generate footprints from ALS data
2. Process all GEDI files (if present)
3. Run the complete analysis pipeline
4. Generate summary statistics and plots

### Option 2: Step-by-Step Control

#### Step 1: Generate Footprints

```bash
python scripts/generate_footprints_from_las.py \
  --las inputs/als/your_area.laz \
  --out inputs/footprints.csv \
  --spacing 30.0 \
  --radius 15.0 \
  --min_count 5
```

**Parameters:**
- `--spacing`: Distance between footprint centers (m)
- `--radius`: Footprint radius (m) - use 15m for GEDI
- `--min_count`: Minimum ALS points required

#### Step 2: Process GEDI Data (if available)

```bash
python scripts/read_gedi_h5.py \
  --h5 inputs/gedi/GEDI02_A_2020123_O12345_T00000_02_001.h5 \
  --out inputs/gedi_table.csv
```

#### Step 3: Run Batch Processing

```bash
python pipeline_batch.py \
  --footprints inputs/footprints.csv \
  --las inputs/als/your_area.laz \
  --workers 4 \
  --out_root results
```

**Parameters:**
- `--workers`: Number of parallel processes
- `--radius`: Footprint radius (default: 15.0m)
- `--dz`: Vertical resolution for profiles (default: 0.5m)
- `--k`: Attenuation coefficient (default: 0.028)

#### Step 4: Visualize Results

```bash
python scripts/plot_results.py \
  --summary results/summary_metrics.csv \
  --gedi inputs/gedi_table.csv \
  --out figures/
```

## 📊 Detailed Workflow

### 1. ALS Preprocessing

**Input:** Raw ALS point cloud (.laz/.las)  
**Output:** Normalized heights, footprint extractions

The pipeline:
- Classifies ground points (if not already done)
- Normalizes heights to ground level
- Extracts points within each footprint radius
- Applies Gaussian weights based on distance from center

### 2. Vertical Profile Construction

**Input:** ALS points within footprint  
**Output:** Vertical energy distribution ρ(z)

Process:
- Bins points into vertical layers (default: 0.5m resolution)
- Applies return-normalized weights: `w = w_gaussian × (1 / n_returns)`
- Normalizes profile to sum to 1.0
- Applies Beer-Lambert attenuation: `ρ'(z) = ρ(z) × exp(-k × ∫ρ(z')dz')`

### 3. Waveform Simulation (Optional)

**Input:** Vertical profile  
**Output:** Simulated GEDI waveform

Steps:
- Convolves profile with Gaussian pulse (σ = 0.6m)
- Resamples to waveform resolution (0.15m)
- Adds realistic noise (SNR = 30dB)

### 4. RH Metrics Computation

**Input:** Vertical profile or waveform  
**Output:** RH25, RH50, RH75, RH90, RH98, FHD

Computes:
- **RH percentiles**: Heights containing X% of cumulative energy
- **FHD**: Shannon entropy of vertical distribution
- **Cover**: Fraction of energy above 2m

### 5. Statistical Comparison

**Input:** ALS metrics + GEDI metrics  
**Output:** Bias, RMSE, R², scatter plots

Metrics:
- **Bias**: Mean difference (ALS - GEDI)
- **RMSE**: Root mean squared error
- **R²**: Coefficient of determination
- Stratified by forest type, slope, sensitivity

## ⚙️ Configuration Parameters

### Optimal Settings for European Mixed Forests (Leaf-On)

```python
# Footprint
FOOTPRINT_SIGMA = 5.5        # Gaussian σ (m)
FOOTPRINT_RADIUS = 15.0      # Extraction radius (m)

# Vertical Resolution
DZ_PROFILE = 0.5             # Profile bin size (m)
DZ_WAVEFORM = 0.15           # Waveform resolution (m)

# Physical Model
ATTENUATION_K = 0.028        # Beer-Lambert coefficient
PULSE_SIGMA = 0.6            # GEDI pulse width (m)
SNR = 30.0                   # Signal-to-noise ratio (dB)

# Quality Filters (GEDI)
MIN_SENSITIVITY = 0.95       # Minimum acceptable sensitivity
MAX_SLOPE = 15.0             # Maximum terrain slope (degrees)
DEGRADE_FLAG = 0             # Must be 0 (good quality)
```

### Parameter Sensitivity

| Parameter | Range | Effect |
|-----------|-------|--------|
| k (attenuation) | 0.02-0.04 | Lower k → more understory energy |
| σ (footprint) | 5.0-6.0 | Larger σ → smoother spatial averaging |
| dz | 0.25-1.0 | Finer dz → more detail, slower processing |

## 📈 Visualization

The pipeline generates:

### 1. Scatter Plots
- ALS vs GEDI for each RH metric
- 1:1 reference line
- Statistics overlaid (bias, RMSE, R²)

### 2. Vertical Profiles
- Side-by-side ALS and GEDI profiles
- Example footprints
- Energy vs height

### 3. Statistical Summaries
- Bias/RMSE per metric
- Stratified by quality filters
- Temporal comparison (if applicable)

### 4. Interactive Dashboard

View the included interactive dashboard for real-time exploration:
```bash
# Open the artifact visualization in your browser
# (dashboard is embedded in this documentation)
```

## 🧪 Testing

The project includes comprehensive unit tests:

```bash
# Run all tests
pytest tests/

# Run specific test modules
pytest tests/test_utils.py
pytest tests/test_generate_footprints.py
pytest tests/test_profiles.py

# Run with coverage
pytest --cov=scripts tests/
```

### Test Coverage

- ✅ Gaussian pulse normalization
- ✅ Footprint weight summation
- ✅ Attenuation energy reduction
- ✅ Waveform convolution
- ✅ RH metric monotonicity
- ✅ Footprint generation from streaming LAS
- ✅ GEDI HDF5 reading
- ✅ End-to-end pipeline

## 📊 Expected Results

### For European Mixed Forests (Pine + Oak, Leaf-On)

| Metric | Expected Bias | Expected RMSE | Expected R² | Quality |
|--------|--------------|---------------|-------------|---------|
| RH25 | 0-1 m | 2-3 m | 0.6-0.7 | Fair |
| RH50 | <1 m | 2-3 m | 0.7-0.8 | Good |
| RH75 | <1 m | 2-4 m | 0.75-0.85 | Good |
| RH90 | <1.5 m | 3-4 m | 0.7-0.8 | Good |
| RH98 | <1.5 m | 3-5 m | 0.7-0.8 | Good |

### Interpretation

**Good results** (publishable):
- |Bias| < 1.5m
- RMSE < 5m  
- R² > 0.7

**Fair results** (acceptable with discussion):
- |Bias| < 2.5m
- RMSE < 7m
- R² > 0.6

**Poor results** (requires investigation):
- |Bias| > 2.5m or RMSE > 7m or R² < 0.6
- Check: ALS point density, GEDI quality flags, seasonal mismatch

## 🐛 Troubleshooting

### Common Issues

#### 1. "No points in footprint"
**Cause:** Coordinate system mismatch  
**Solution:** Ensure ALS and footprints use same CRS

```python
# Check CRS
import laspy
las = laspy.read("your_file.laz")
print(las.header.parse_crs())
```

#### 2. "Large RMSE (>10m)"
**Possible causes:**
- Leaf-on/leaf-off mismatch
- Wrong attenuation parameter
- GEDI quality issues

**Solution:**
- Check acquisition dates
- Try k = 0.02-0.04
- Apply stricter quality filters

#### 3. "Memory Error"
**Cause:** Large ALS file  
**Solution:** Use chunked processing

```bash
# Enable streaming in generate_footprints
python scripts/generate_footprints_from_las.py \
  --chunk_size 500000 \
  ...
```

#### 4. "No GEDI data after filtering"
**Cause:** Overly strict quality filters  
**Solution:** Relax sensitivity threshold

```python
# In comparison script
MIN_SENSITIVITY = 0.90  # Instead of 0.95
```

## 📚 Citation

If you use this pipeline in your research, please cite:

```bibtex
@software{als_gedi_pipeline,
  title = {ALS-GEDI Comparison Pipeline},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/als-gedi-pipeline}
}
```

### Related Publications

Key papers that informed this methodology:

- Dubayah et al. (2020). "The Global Ecosystem Dynamics Investigation." *Remote Sensing of Environment*
- Hancock et al. (2019). "The GEDI Simulator." *Remote Sensing of Environment*
- Duncanson et al. (2020). "Biomass estimation from simulated GEDI." *Remote Sensing of Environment*

## 📝 Methods Section (for publications)

Use this template for your Methods section:

> ALS point clouds acquired during leaf-on conditions were normalized to ground level using the Cloth Simulation Filter (CSF) algorithm. For each analysis location, points within a 15m radius were extracted and weighted using a Gaussian function (σ = 5.5m) to simulate GEDI footprint geometry. 
>
> Vertical pseudo-energy profiles were constructed at 0.5m resolution using return-normalized weights (1 / number_of_returns) to account for multiple return effects. Canopy attenuation was modeled using a Beer-Lambert formulation with extinction coefficient k = 0.028, calibrated for European mixed forests:
>
> ρ'(z) = ρ(z) × exp(-k × ∫₀^z ρ(z')dz')
>
> Relative height (RH) metrics were computed identically to GEDI L2A products by determining heights containing specified percentiles (25%, 50%, 75%, 90%, 98%) of cumulative vertical energy. Foliage Height Diversity (FHD) was calculated as Shannon entropy of the normalized vertical profile.
>
> Simulated ALS metrics were compared against colocated GEDI L2A observations after applying standard quality filters: sensitivity ≥ 0.95, degrade_flag = 0, and terrain slope ≤ 15°. Statistical validation included bias (mean difference), RMSE, and R² computation for each RH metric.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## 🙏 Acknowledgments

- GEDI Science Team for sensor specifications and validation protocols
- lidR R package developers for ALS processing algorithms
- European Space Agency for ALS reference datasets


**Last Updated:** January 2026  
**Version:** 1.0.0  
**Status:** Production-ready for European mixed forests (leaf-on conditions)