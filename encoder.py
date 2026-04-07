#!/usr/bin/env python3
"""
Digilog Encoder v0.1
====================
Encodes an MP3 into a .dtw (Dotwave) file and renders a printable colored dot grid.

Usage:
    python3 encoder.py <input.mp3> [--duration 30] [--format card]

Formats:
    sticker     50x50mm
    card        85x55mm  (default)
    cd          120x120mm
    postcard    148x105mm
    a5          210x148mm
    a4          210x297mm

License: GPL v3 — free forever, open forever
github.com/pisdronio/digilog-spec
"""

import os
import sys
import json
import struct
import hashlib
import argparse
import subprocess
import tempfile
from pathlib import Path


# ─── Format definitions ───────────────────────────────────────────────────────

FORMATS = {
    'sticker':  {'w_mm': 50,  'h_mm': 50,  'label': 'Sticker 50x50mm'},
    'card':     {'w_mm': 85,  'h_mm': 55,  'label': 'Business Card 85x55mm'},
    'cd':       {'w_mm': 120, 'h_mm': 120, 'label': 'CD Inlay 120x120mm'},
    'postcard': {'w_mm': 148, 'h_mm': 105, 'label': 'Postcard 148x105mm'},
    'a5':       {'w_mm': 210, 'h_mm': 148, 'label': 'A5 Flyer 210x148mm'},
    'a4':       {'w_mm': 210, 'h_mm': 297, 'label': 'A4 Poster 210x297mm'},
}

# Opus stream bitrates per ring layer
LAYER_BITRATES = [6, 12, 24]  # kbps — core, enhancement 1, enhancement 2

# DTW file magic bytes
DTW_MAGIC = b'DTW1'
DTW_VERSION = 1
CODEC_OPUS = 0x01

# 8 colors for dot grid (3 bits per dot)
# Each color maps to a 3-bit value 0-7
COLORS = [
    (0,   0,   0  ),  # 0 — black
    (255, 255, 255),  # 1 — white
    (220, 50,  50 ),  # 2 — red
    (50,  180, 50 ),  # 3 — green
    (50,  50,  220),  # 4 — blue
    (220, 180, 50 ),  # 5 — yellow
    (180, 50,  220),  # 6 — purple
    (50,  200, 200),  # 7 — cyan
]

DPI = 300
MODULE_PX = 4  # dots per module at 300 DPI


# ─── Step 1: Encode audio into 3 Opus streams ─────────────────────────────────

def encode_audio_layers(input_mp3, duration_sec, tmpdir):
    """Encode input MP3 into 3 Opus streams at 6/12/24 kbps."""
    print(f"\n[1/4] Encoding audio layers from {Path(input_mp3).name}")

    # Normalize and trim to mono WAV first
    wav_path = os.path.join(tmpdir, 'source.wav')
    cmd = [
        'ffmpeg', '-y', '-i', input_mp3,
        '-ss', '0', '-t', str(duration_sec),
        '-ac', '1', '-ar', '44100',
        '-af', 'loudnorm',
        wav_path
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print("  Warning: loudnorm failed, trying without normalization")
        cmd = [
            'ffmpeg', '-y', '-i', input_mp3,
            '-ss', '0', '-t', str(duration_sec),
            '-ac', '1', '-ar', '44100',
            wav_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)

    layers = []
    for i, kbps in enumerate(LAYER_BITRATES):
        opus_path = os.path.join(tmpdir, f'layer_{i}_{kbps}k.opus')
        cmd = [
            'ffmpeg', '-y', '-i', wav_path,
            '-c:a', 'libopus',
            '-b:a', f'{kbps}k',
            '-vbr', 'off',
            opus_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        size = os.path.getsize(opus_path)
        print(f"  Layer {i} ({kbps} kbps): {size:,} bytes")
        with open(opus_path, 'rb') as f:
            layers.append(f.read())

    actual_duration = duration_sec
    return layers, actual_duration


# ─── Step 2: Pack layers into .dtw file ───────────────────────────────────────

def pack_dtw(layers, duration_sec, metadata, output_path):
    """Pack 3 audio layers into a .dtw binary file."""
    print(f"\n[2/4] Packing .dtw file")

    meta_json = json.dumps(metadata, ensure_ascii=False).encode('utf-8')

    with open(output_path, 'wb') as f:
        # Magic + version
        f.write(DTW_MAGIC)
        f.write(struct.pack('B', DTW_VERSION))

        # Codec
        f.write(struct.pack('B', CODEC_OPUS))

        # Duration (uint16, seconds)
        f.write(struct.pack('>H', int(duration_sec)))

        # Layer count
        f.write(struct.pack('B', len(layers)))

        # Metadata length + metadata
        f.write(struct.pack('>H', len(meta_json)))
        f.write(meta_json)

        # Each layer: length (uint32) + data + CRC32
        for i, layer_data in enumerate(layers):
            crc = hashlib.new('crc32c') if 'crc32c' in hashlib.algorithms_available else None
            import binascii
            crc_val = binascii.crc32(layer_data) & 0xFFFFFFFF
            f.write(struct.pack('>I', len(layer_data)))
            f.write(layer_data)
            f.write(struct.pack('>I', crc_val))
            print(f"  Layer {i}: {len(layer_data):,} bytes, CRC32={crc_val:#010x}")

    total_size = os.path.getsize(output_path)
    print(f"  .dtw file: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    return total_size


# ─── Step 3: Render dot grid image ────────────────────────────────────────────

def bytes_to_bits(data):
    """Convert bytes to a list of bits."""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits

def bits_to_trits(bits):
    """Group bits into 3-bit values (0-7) for 8-color encoding."""
    trits = []
    for i in range(0, len(bits) - 2, 3):
        val = (bits[i] << 2) | (bits[i+1] << 1) | bits[i+2]
        trits.append(val)
    return trits

# Calibration strip height in modules
CALIB_MODULES_H = 4

def render_dot_grid(dtw_path, fmt, output_png):
    """Render .dtw file as a printable colored dot grid PNG with calibration strip."""
    print(f"\n[3/4] Rendering dot grid ({fmt['label']})")

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  Installing Pillow...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow', '--break-system-packages', '-q'], check=True)
        from PIL import Image, ImageDraw, ImageFont

    # Calculate grid dimensions
    w_px  = int((fmt['w_mm'] / 25.4) * DPI)
    h_px  = int((fmt['h_mm'] / 25.4) * DPI)
    margin = MODULE_PX * 4
    grid_w = (w_px - margin * 2) // MODULE_PX
    calib_px = CALIB_MODULES_H * MODULE_PX        # calibration strip height in px
    data_h_px = h_px - margin * 2 - calib_px - 4  # leave 4px gap between data and strip
    grid_h    = data_h_px // MODULE_PX
    total_modules = grid_w * grid_h
    total_bits    = total_modules * 3

    print(f"  Canvas: {w_px}x{h_px}px")
    print(f"  Data grid: {grid_w}x{grid_h} modules = {total_modules:,} modules")
    print(f"  Capacity: {total_bits//8:,} bytes")
    print(f"  Calibration strip: {grid_w}x{CALIB_MODULES_H} modules")

    # Read .dtw file
    with open(dtw_path, 'rb') as f:
        dtw_data = f.read()

    # Convert to color indices
    bits = bytes_to_bits(dtw_data)
    while len(bits) < total_bits:
        bits.append(0)
    bits = bits[:total_bits]
    color_indices = bits_to_trits(bits)

    # Create image
    img = Image.new('RGB', (w_px, h_px), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # ── Finder patterns (3 corners) ──────────────────────────────────────────
    fp_size = MODULE_PX * 7
    for fx, fy in [(margin, margin),
                   (w_px - margin - fp_size, margin),
                   (margin, h_px - margin - fp_size - calib_px - 8)]:
        draw.rectangle([fx, fy, fx + fp_size, fy + fp_size], fill=(0, 0, 0))
        draw.rectangle([fx + MODULE_PX, fy + MODULE_PX,
                        fx + fp_size - MODULE_PX, fy + fp_size - MODULE_PX], fill=(255, 255, 255))
        draw.rectangle([fx + MODULE_PX*2, fy + MODULE_PX*2,
                        fx + fp_size - MODULE_PX*2, fy + fp_size - MODULE_PX*2], fill=(0, 0, 0))

    # ── Data modules ──────────────────────────────────────────────────────────
    idx = 0
    for row in range(grid_h):
        for col in range(grid_w):
            if idx >= len(color_indices):
                break
            color = COLORS[color_indices[idx]]
            x = margin + col * MODULE_PX
            y = margin + row * MODULE_PX
            draw.rectangle([x, y, x + MODULE_PX - 1, y + MODULE_PX - 1], fill=color)
            idx += 1

    # ── Layer boundary lines (subtle visual guides) ───────────────────────────
    third_h = (grid_h * MODULE_PX) // 3
    for i in range(1, 3):
        y_line = margin + third_h * i
        draw.line([(margin, y_line), (w_px - margin, y_line)],
                  fill=(200, 200, 200), width=1)

    # ── Calibration strip ─────────────────────────────────────────────────────
    strip_y = margin + grid_h * MODULE_PX + 4  # 4px gap below data
    # Thin separator line
    draw.line([(margin, strip_y - 2), (w_px - margin, strip_y - 2)],
              fill=(180, 180, 180), width=1)

    # Fill strip with all 8 colors repeating across full width
    for col in range(grid_w):
        color_idx = col % len(COLORS)
        color = COLORS[color_idx]
        x = margin + col * MODULE_PX
        for row in range(CALIB_MODULES_H):
            y = strip_y + row * MODULE_PX
            draw.rectangle([x, y, x + MODULE_PX - 1, y + MODULE_PX - 1], fill=color)

    print(f"  Calibration strip drawn at y={strip_y}px")

    img.save(output_png, dpi=(DPI, DPI))
    print(f"  Saved: {output_png}")
    return w_px, h_px, grid_w, grid_h


# ─── Step 4: Print summary ────────────────────────────────────────────────────

def print_summary(input_mp3, dtw_path, png_path, layers, duration_sec, fmt, grid_w, grid_h):
    print(f"\n[4/4] Digilog encode complete")
    print(f"  {'─' * 45}")
    print(f"  Format:      {fmt['label']}")
    print(f"  Source:      {Path(input_mp3).name}")
    print(f"  Duration:    {duration_sec}s")
    print(f"  Grid:        {grid_w}x{grid_h} modules")
    print(f"  .dtw file:   {Path(dtw_path).name} ({os.path.getsize(dtw_path)/1024:.1f} KB)")
    print(f"  Print file:  {Path(png_path).name}")
    print(f"  {'─' * 45}")
    print(f"  Layer 0 (core,  6kbps): {len(layers[0]):,} bytes")
    print(f"  Layer 1 (enh1, 12kbps): {len(layers[1]):,} bytes")
    print(f"  Layer 2 (enh2, 24kbps): {len(layers[2]):,} bytes")
    print(f"  Total audio:            {sum(len(l) for l in layers):,} bytes")
    print(f"\n  Scan the groove. 🎵")


# ─── Main ─────────────────────────────────────────────────────────────────────


def add_label(png_path, metadata, fmt):
    """Add minimal artist/title label below the dot grid. Just the human identity of the music."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(png_path)
    w, h = img.size

    artist = metadata.get('artist', '').strip()
    title  = metadata.get('title', '').strip()

    # Only add label if we have something to show
    if not artist and not title:
        return

    try:
        font_artist = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 28)
        font_title  = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
    except:
        font_artist = ImageFont.load_default()
        font_title  = font_artist

    padding    = 24
    line_gap   = 10
    artist_h   = 34 if artist else 0
    title_h    = 28 if title  else 0
    label_h    = padding + artist_h + (line_gap if artist and title else 0) + title_h + padding

    new_img = Image.new('RGB', (w, h + label_h), (255, 255, 255))
    new_img.paste(img, (0, 0))
    draw = ImageDraw.Draw(new_img)

    # Thin separator line
    draw.line([(padding, h + 1), (w - padding, h + 1)], fill=(220, 220, 220), width=1)

    y = h + padding
    if artist:
        draw.text((padding, y), artist, font=font_artist, fill=(20, 20, 20))
        y += artist_h + line_gap
    if title:
        draw.text((padding, y), title, font=font_title, fill=(100, 100, 100))

    new_img.save(png_path, dpi=(DPI, DPI))
    print(f"  Label added: {artist} — {title}")

def main():
    parser = argparse.ArgumentParser(description='Digilog Encoder v0.1 — encode audio to .dtw dotwave file')
    parser.add_argument('input',          help='Input MP3 file')
    parser.add_argument('--duration',     type=int, default=30,             help='Duration in seconds (default: 30)')
    parser.add_argument('--format',       default='card', choices=FORMATS.keys(), help='Print format (default: card)')
    parser.add_argument('--artist',       default='Unknown Artist',         help='Artist name')
    parser.add_argument('--title',        default='Unknown Title',          help='Track title')
    parser.add_argument('--album',        default='',                       help='Album name')
    parser.add_argument('--year',         default='',                       help='Release year')
    parser.add_argument('--genre',        default='',                       help='Genre')
    parser.add_argument('--track',        default='',                       help='Track number')
    parser.add_argument('--mb-recording', default='',                       help='MusicBrainz recording MBID')
    parser.add_argument('--mb-artist',    default='',                       help='MusicBrainz artist MBID')
    parser.add_argument('--mb-release',   default='',                       help='MusicBrainz release MBID')
    parser.add_argument('--composer',     default='',                       help='Composer / songwriter name')
    parser.add_argument('--bpm',          default='',                       help='BPM / tempo')
    parser.add_argument('--isrc',         default='',                       help='ISRC code (international recording ID)')
    parser.add_argument('--license',      default='All rights reserved',    help='Rights/license string')
    parser.add_argument('--output',       default=None,                     help='Output filename (without extension)')
    args = parser.parse_args()

    fmt = FORMATS[args.format]
    input_path = args.input
    base_name = args.output or Path(input_path).stem
    dtw_path = f'{base_name}.dtw'
    png_path = f'{base_name}_digilog_{args.format}.png'

    metadata = {
        'title':            args.title,
        'artist':           args.artist,
        'album':            args.album,
        'year':             args.year,
        'genre':            args.genre,
        'track':            args.track,
        'mb_recording_id':  getattr(args, 'mb_recording', ''),
        'mb_artist_id':     getattr(args, 'mb_artist', ''),
        'mb_release_id':    getattr(args, 'mb_release', ''),
        'license':          args.license,
        'digilog_version':  '0.1',
        'digilog_format':   args.format,
        'digilog_layers':   3,
        'digilog_bitrates': LAYER_BITRATES,
        'composer':         args.composer,
        'bpm':              args.bpm,
        'isrc':             args.isrc,
        'digilog_spec':     'github.com/pisdronio/digilog-spec',
    }

    print(f"\n  Digilog Encoder v0.1")
    print(f"  github.com/pisdronio/digilog-spec")
    print(f"  {'─' * 45}")

    with tempfile.TemporaryDirectory() as tmpdir:
        layers, duration = encode_audio_layers(input_path, args.duration, tmpdir)
        pack_dtw(layers, duration, metadata, dtw_path)
        grid_w, grid_h = render_dot_grid(dtw_path, fmt, png_path)[2:4]
        add_label(png_path, metadata, fmt)
        print_summary(input_path, dtw_path, png_path, layers, duration, fmt, grid_w, grid_h)


if __name__ == '__main__':
    main()


