#!/usr/bin/env python3
"""
Digilog Decoder v0.1
====================
Decodes a .dtw file or a scanned Digilog PNG image and plays the audio.

Usage:
    python3 decoder.py <input.dtw>           # decode from .dtw file directly
    python3 decoder.py <input.png>           # decode from scanned image
    python3 decoder.py <input.dtw> --info    # show metadata only, no playback
    python3 decoder.py <input.dtw> --layer 0 # force specific layer (0=core, 1=enh1, 2=enh2)
    python3 decoder.py <input.dtw> --save output.mp3  # save to file instead of playing

License: GPL v3 — free forever, open forever
github.com/pisdronio/digilog-spec
"""

import os
import sys
import json
import struct
import binascii
import argparse
import tempfile
import subprocess
from pathlib import Path


# ─── Constants (must match encoder) ──────────────────────────────────────────

DTW_MAGIC   = b'DTW1'
DTW_VERSION = 1
CODEC_OPUS  = 0x01

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

DPI       = 300
MODULE_PX = 4


# ─── Step 1: Parse .dtw file ──────────────────────────────────────────────────

def parse_dtw(dtw_path):
    """Parse a .dtw binary file into header, metadata and audio layers."""
    with open(dtw_path, 'rb') as f:
        data = f.read()

    offset = 0

    # Magic
    magic = data[offset:offset+4]
    offset += 4
    if magic != DTW_MAGIC:
        raise ValueError(f"Not a valid Digilog file (magic bytes: {magic})")

    # Version
    version = data[offset]
    offset += 1

    # Codec
    codec = data[offset]
    offset += 1

    # Duration
    duration = struct.unpack_from('>H', data, offset)[0]
    offset += 2

    # Layer count
    layer_count = data[offset]
    offset += 1

    # Metadata
    meta_len = struct.unpack_from('>H', data, offset)[0]
    offset += 2
    meta_json = data[offset:offset+meta_len].decode('utf-8')
    metadata = json.loads(meta_json) if meta_json.strip() else {}
    offset += meta_len

    # Layers
    layers = []
    for i in range(layer_count):
        layer_len = struct.unpack_from('>I', data, offset)[0]
        offset += 4
        layer_data = data[offset:offset+layer_len]
        offset += layer_len
        stored_crc = struct.unpack_from('>I', data, offset)[0]
        offset += 4

        # Verify CRC
        actual_crc = binascii.crc32(layer_data) & 0xFFFFFFFF
        if actual_crc != stored_crc:
            print(f"  Warning: Layer {i} CRC mismatch — data may be corrupted")
            layers.append({'data': layer_data, 'valid': False, 'size': layer_len})
        else:
            layers.append({'data': layer_data, 'valid': True, 'size': layer_len})

    return {
        'version':     version,
        'codec':       codec,
        'duration':    duration,
        'layer_count': layer_count,
        'metadata':    metadata,
        'layers':      layers,
    }


# ─── Step 2: Decode PNG image to .dtw ────────────────────────────────────────

def nearest_color(pixel, colors):
    """Find the nearest color index for a given pixel."""
    import numpy as np
    dists = [sum((int(pixel[c]) - colors[i][c])**2 for c in range(3)) for i in range(len(colors))]
    return dists.index(min(dists))

def decode_png_to_dtw(png_path, output_dtw):
    """Scan a Digilog PNG image and extract the .dtw data."""
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'Pillow', 'numpy',
                       '--break-system-packages', '-q'], check=True)
        from PIL import Image
        import numpy as np

    print(f"\n[scan] Reading image: {png_path}")
    img = Image.open(png_path).convert('RGB')
    w, h = img.size
    pixels = np.array(img)

    # Crop label area — find where white rows start at bottom
    # (label area is pure white rows below the dot grid)
    row_means = pixels.mean(axis=(1,2))
    grid_h = h
    for row in range(h-1, h//2, -1):
        if row_means[row] < 250:
            grid_h = row + 1
            break

    print(f"  Image: {w}x{h}px, grid area: {w}x{grid_h}px")

    # Calculate margins and grid
    margin   = MODULE_PX * 4
    grid_w   = (w - margin * 2) // MODULE_PX
    grid_rows = (grid_h - margin * 2) // MODULE_PX

    print(f"  Grid: {grid_w}x{grid_rows} modules")

    # Read color of each module (sample center pixel)
    color_indices = []
    for row in range(grid_rows):
        for col in range(grid_w):
            cx = margin + col * MODULE_PX + MODULE_PX // 2
            cy = margin + row * MODULE_PX + MODULE_PX // 2
            pixel = pixels[cy, cx]
            idx = nearest_color(pixel, COLORS)
            color_indices.append(idx)

    # Convert color indices to bits (3 bits per module)
    bits = []
    for idx in color_indices:
        bits.append((idx >> 2) & 1)
        bits.append((idx >> 1) & 1)
        bits.append(idx & 1)

    # Convert bits to bytes
    byte_data = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for b in range(8):
            byte = (byte << 1) | bits[i + b]
        byte_data.append(byte)

    with open(output_dtw, 'wb') as f:
        f.write(byte_data)

    print(f"  Extracted: {len(byte_data):,} bytes → {output_dtw}")
    return output_dtw


# ─── Step 3: Select best valid layer ─────────────────────────────────────────

def select_layer(parsed, force_layer=None):
    """Select the best available valid layer, or a forced specific layer."""
    layers = parsed['layers']
    bitrates = [6, 12, 24]

    if force_layer is not None:
        if force_layer < len(layers):
            layer = layers[force_layer]
            print(f"\n[layer] Forced layer {force_layer} ({bitrates[force_layer]} kbps) — valid: {layer['valid']}")
            return force_layer, layer
        else:
            print(f"  Layer {force_layer} not available, falling back to best")

    # Pick highest valid layer
    for i in range(len(layers) - 1, -1, -1):
        if layers[i]['valid']:
            print(f"\n[layer] Best readable layer: {i} ({bitrates[i] if i < len(bitrates) else '?'} kbps)")
            return i, layers[i]

    # If no valid layer, try anyway with layer 0
    print("\n[layer] Warning: no fully valid layer found, attempting core layer anyway")
    return 0, layers[0]


# ─── Step 4: Play or save audio ───────────────────────────────────────────────

def play_or_save(layer_data, codec, duration, save_path=None):
    """Decode Opus layer and play or save as audio."""
    with tempfile.TemporaryDirectory() as tmpdir:
        opus_path = os.path.join(tmpdir, 'audio.opus')
        with open(opus_path, 'wb') as f:
            f.write(layer_data)

        if save_path:
            # Save to file
            ext = Path(save_path).suffix.lower()
            codec_map = {'.mp3': 'libmp3lame', '.wav': 'pcm_s16le', '.ogg': 'libvorbis', '.opus': 'copy'}
            acodec = codec_map.get(ext, 'libmp3lame')
            cmd = ['ffmpeg', '-y', '-i', opus_path, '-c:a', acodec, save_path]
            subprocess.run(cmd, capture_output=True, check=True)
            print(f"\n[save] Saved to: {save_path}")
        else:
            # Play directly
            print(f"\n[play] Playing {duration}s of audio...")
            print(f"       Press Ctrl+C to stop\n")

            # Try different players
            players = [
                ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', opus_path],
                ['aplay', opus_path],
                ['paplay', opus_path],
            ]
            played = False
            for player_cmd in players:
                try:
                    subprocess.run(player_cmd, check=True)
                    played = True
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue

            if not played:
                # Save as mp3 fallback
                fallback = 'digilog_playback.mp3'
                cmd = ['ffmpeg', '-y', '-i', opus_path, '-c:a', 'libmp3lame', '-q:a', '2', fallback]
                subprocess.run(cmd, capture_output=True, check=True)
                print(f"  Could not play directly — saved as {fallback}")
                print(f"  Open it in any audio player")


# ─── Step 5: Print metadata ───────────────────────────────────────────────────

def print_metadata(parsed):
    """Pretty print the metadata from a .dtw file."""
    meta = parsed['metadata']
    layers = parsed['layers']
    bitrates = [6, 12, 24]

    print(f"\n  {'─' * 45}")
    print(f"  Digilog Decoder v0.1")
    print(f"  {'─' * 45}")

    artist = meta.get('artist', '')
    title  = meta.get('title', '')
    if artist or title:
        print(f"  {artist} — {title}" if artist and title else f"  {artist or title}")

    if meta.get('album'):    print(f"  Album:    {meta['album']}")
    if meta.get('year'):     print(f"  Year:     {meta['year']}")
    if meta.get('genre'):    print(f"  Genre:    {meta['genre']}")
    if meta.get('composer'): print(f"  Composer: {meta['composer']}")
    if meta.get('bpm'):      print(f"  BPM:      {meta['bpm']}")
    if meta.get('isrc'):     print(f"  ISRC:     {meta['isrc']}")

    print(f"\n  Duration: {parsed['duration']}s")
    print(f"  Layers:   {parsed['layer_count']}")

    for i, layer in enumerate(layers):
        br = bitrates[i] if i < len(bitrates) else '?'
        status = 'ok' if layer['valid'] else 'corrupted'
        print(f"    Layer {i} ({br} kbps): {layer['size']:,} bytes [{status}]")

    mb_rec = meta.get('mb_recording_id', '')
    mb_art = meta.get('mb_artist_id', '')
    mb_rel = meta.get('mb_release_id', '')
    if any([mb_rec, mb_art, mb_rel]):
        print(f"\n  MusicBrainz:")
        if mb_rec: print(f"    Recording: {mb_rec}")
        if mb_art: print(f"    Artist:    {mb_art}")
        if mb_rel: print(f"    Release:   {mb_rel}")

    if meta.get('license'):
        print(f"\n  License: {meta['license']}")

    print(f"\n  Spec: {meta.get('digilog_spec', 'github.com/pisdronio/digilog-spec')}")
    print(f"  {'─' * 45}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Digilog Decoder v0.1 — decode .dtw or scanned PNG to audio')
    parser.add_argument('input',          help='Input .dtw file or scanned PNG image')
    parser.add_argument('--info',         action='store_true', help='Show metadata only, no playback')
    parser.add_argument('--layer',        type=int, default=None, help='Force specific layer (0=core, 1=enh1, 2=enh2)')
    parser.add_argument('--save',         default=None, help='Save audio to file instead of playing (e.g. output.mp3)')
    args = parser.parse_args()

    input_path = args.input
    ext = Path(input_path).suffix.lower()

    print(f"\n  Digilog Decoder v0.1")
    print(f"  github.com/pisdronio/digilog-spec")
    print(f"  {'─' * 45}")

    # If PNG input, extract .dtw first
    if ext in ['.png', '.jpg', '.jpeg']:
        print(f"\n[mode] Image scan mode")
        with tempfile.TemporaryDirectory() as tmpdir:
            dtw_path = os.path.join(tmpdir, 'decoded.dtw')
            decode_png_to_dtw(input_path, dtw_path)
            parsed = parse_dtw(dtw_path)
    elif ext == '.dtw':
        print(f"\n[mode] Direct .dtw decode")
        parsed = parse_dtw(input_path)
    else:
        print(f"  Error: unsupported file type '{ext}' — use .dtw or .png")
        sys.exit(1)

    # Always show metadata
    print_metadata(parsed)

    if args.info:
        return

    # Select and play layer
    layer_idx, layer = select_layer(parsed, args.layer)
    play_or_save(layer['data'], parsed['codec'], parsed['duration'], args.save)

    print("\n  Scan the groove. 🎵\n")


if __name__ == '__main__':
    main()
