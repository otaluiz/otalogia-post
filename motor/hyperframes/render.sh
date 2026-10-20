#!/usr/bin/env bash
# Uso: bash motor/hyperframes/render.sh carrosseis/<slug>
# Renderiza carrosseis/<slug>/motion/index.html (HyperFrames, 6 s por slide) e corta um MP4 por slide em motion/out/.
# Fontes, CSS/JS do tema e as imagens do carrossel são copiados para motion/ na hora (não versionar: ver .gitignore).
set -e
DIR=$(cd "$1/motion" && pwd); HF=$(cd "$(dirname "$0")" && pwd)
cd "$DIR"
cp -r "$HF/fonts" "$HF/otalogia.css" "$HF/otalogia.js" .
mkdir -p img out && cp ../*.png img/
npx -y hyperframes@0.8.181 render --quality looks --output out/completo.mp4
N=$(grep -c '<section' index.html)
for i in $(seq 1 "$N"); do
  ffmpeg -y -loglevel error -ss $(( (i-1)*6 )) -t 6 -i out/completo.mp4 -c:v libx264 -crf 17 -pix_fmt yuv420p -movflags +faststart out/slide-$(printf %02d "$i").mp4
done
echo "ok: $DIR/out ($N slides)"
