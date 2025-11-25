# Conda Installation Guide for EcoSight

## Option 1: Using environment.yml

```bash
# Create conda environment from file
conda env create -f environment.yml

# Activate the environment
conda activate ecosight

# Verify installation
python -c "import tensorflow as tf; print('TensorFlow:', tf.__version__)"
python -c "import streamlit; print('Streamlit installed')"
python -c "import fastapi; print('FastAPI installed')"
```
