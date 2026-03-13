#!/bin/bash
INPUT_DIR="assets/images/tiles"
OUTPUT_DIR="assets/data/svg_traces"

mkdir -p "$OUTPUT_DIR"

for img in "$INPUT_DIR"/*.png; do
    filename=$(basename -- "$img")
    name="${filename%.*}"
    echo "Processing $filename..."

    # Step 1: Create a temporary high-contrast PNG mask
    # (Assume opaque = shape, transparent = background)
    convert "$img" -alpha extract -negate /tmp/"$name"_mask.pbm

    # Step 2: Trace the mask to an SVG path using potrace
    # Options: --tightens to simplify, --turnpolicy white to treat white as background
    potrace -s --tighten=0.2 --turnpolicy white /tmp/"$name"_mask.pbm -o "$OUTPUT_DIR/$name.svg"

    rm /tmp/"$name"_mask.pbm
    echo "  -> Saved SVG trace to $OUTPUT_DIR/$name.svg"
done

echo "Done. You can now open the SVG files in a vector editor or use a script to extract the path data."

