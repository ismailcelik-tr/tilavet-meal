#!/bin/sh
# Fetch sherpa-onnx for iOS and copy the model and data the app bundles (both gitignored).
#
#     sh scripts/ios_resources.sh
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
APP="$ROOT/ios/TilavetApp"
SHERPA_TAG=v2.0.0
SHERPA_ZIP="sherpa-onnx-$SHERPA_TAG-ios-shared-onnxruntime-static.xcframework.zip"

mkdir -p "$APP/Vendor" "$APP/Data"
if [ ! -d "$APP/Vendor/SherpaOnnxC.xcframework" ]; then
    curl -sfL -o "$APP/Vendor/sherpa.zip" "https://github.com/k2-fsa/sherpa-onnx/releases/download/xcframework/$SHERPA_ZIP"
    unzip -q -o "$APP/Vendor/sherpa.zip" -d "$APP/Vendor"
    rm "$APP/Vendor/sherpa.zip"
fi
curl -sfL -o "$APP/Vendor/SherpaOnnx.swift" \
    "https://raw.githubusercontent.com/k2-fsa/sherpa-onnx/$SHERPA_TAG/swift-api-examples/SherpaOnnx.swift"

cd "$ROOT"
uv run --group onnx python -c "
from huggingface_hub import hf_hub_download
for f in ('model.int8.onnx', 'tokens.txt', 'spelling.json'):
    print(hf_hub_download('Abdou/quran-asr-tiny', f))
" | while read -r path; do cp "$path" "$APP/Data/"; done

cp data/raw/quran-simple-clean.txt data/raw/tr.diyanet.txt data/derived/meal-durations-tr.diyanet-yelda.csv "$APP/Data/"
rsync -a --delete --exclude '*.part.m4a' data/derived/meals/tr.diyanet-yelda/ "$APP/Data/meals/"
echo "resources: $(du -sh "$APP/Data" | cut -f1)"
