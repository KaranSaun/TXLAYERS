#!/bin/bash

set -e

echo "Creating models cache directory..."
mkdir -p models_cache

echo "Downloading Real-ESRGAN model..."
if [ ! -f "models_cache/RealESRGAN_x4plus.pth" ]; then
    curl -L -o models_cache/RealESRGAN_x4plus.pth \
      https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
    echo "✓ Real-ESRGAN model downloaded"
else
    echo "✓ Real-ESRGAN model already exists"
fi

echo "Downloading SAM2 model..."
if [ ! -f "models_cache/sam2_hiera_base_plus.pt" ]; then
    curl -L -o models_cache/sam2_hiera_base_plus.pt \
      https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_base_plus.pt
    echo "✓ SAM2 model downloaded"
else
    echo "✓ SAM2 model already exists"
fi

echo ""
echo "All models downloaded successfully!"
echo "Note: rembg (u2net) will download automatically on first run."
