# Magic Solution Pro

A Streamlit app for calculating buffer preparation and pH adjustment using SciPy's nonlinear solver.

## Overview

`Magic Solution Pro` computes the amount of buffer powder and titrant needed to prepare a target volume of buffer solution at a desired pH and temperature. It uses a charge balance equation and performs nonlinear optimization with SciPy to estimate the required strong acid or base.

## Features

- Adjustable target pH, temperature, and final volume
- Select from common biological buffers in free acid form
- Define buffer concentration and supporting salt composition
- Computes thermodynamic pK at the chosen temperature
- Estimates total ionic strength including titrant contribution
- Provides a lab-ready recipe with powder mass and titrant volume

## Buffers Supported

The app includes the following buffer systems:

- MES
- Cacodyl
- Bistris
- ADA
- ACES
- PIPES
- BES
- Imidazl
- MOPS
- TES
- HEPES
- HEPPS
- Tris

## Installation

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the App

Start the Streamlit application with:

```bash
streamlit run app.py
```

Then open the URL shown in the terminal to interact with the calculator.

## Notes

- The app assumes a 1:1 titrant (KOH/NaOH or HCl) for pH adjustment.
- Buffer mass is calculated from the total buffer concentration, molar mass, and final volume.
- Ionic strength is estimated from buffer speciation, salts, and titrant addition.
