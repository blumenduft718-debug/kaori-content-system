#!/bin/bash
# ダウンロードフォルダ整理スクリプト
# PDF / 画像 / Excel をそれぞれのフォルダに仕分けします

DOWNLOADS="$HOME/Downloads"

if [ ! -d "$DOWNLOADS" ]; then
  echo "ダウンロードフォルダが見つかりません: $DOWNLOADS"
  exit 1
fi

# サブフォルダを作成（存在しない場合のみ）
mkdir -p "$DOWNLOADS/PDF"
mkdir -p "$DOWNLOADS/画像"
mkdir -p "$DOWNLOADS/Excel"

moved=0

# PDF を移動
for f in "$DOWNLOADS"/*.pdf "$DOWNLOADS"/*.PDF; do
  [ -f "$f" ] || continue
  mv "$f" "$DOWNLOADS/PDF/"
  echo "移動: $(basename "$f") → PDF/"
  ((moved++))
done

# 画像を移動
for ext in jpg jpeg png gif webp bmp svg tiff tif JPG JPEG PNG GIF WEBP BMP SVG TIFF TIF; do
  for f in "$DOWNLOADS"/*."$ext"; do
    [ -f "$f" ] || continue
    mv "$f" "$DOWNLOADS/画像/"
    echo "移動: $(basename "$f") → 画像/"
    ((moved++))
  done
done

# Excel を移動
for ext in xlsx xls xlsm XLSX XLS XLSM; do
  for f in "$DOWNLOADS"/*."$ext"; do
    [ -f "$f" ] || continue
    mv "$f" "$DOWNLOADS/Excel/"
    echo "移動: $(basename "$f") → Excel/"
    ((moved++))
  done
done

echo ""
echo "完了: ${moved}件のファイルを移動しました"
