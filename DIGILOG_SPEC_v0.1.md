# Digilog Format Specification
## Version 0.1 — First Draft
**Status:** Working draft  
**License:** GPL v3 — free forever, open forever  
**File extension:** `.dtw` (dotwave)  
**The verb:** "scan the groove"

---

## What is Digilog?

Digilog is a free, open, physical audio format.

### The founding principle

**Physical motion through a Digilog code is motion through time in the audio.**

A Digilog code encodes audio spatially — time compressed into space.
The decoder does not simply play a file. It maps physical movement to audio playback:

| Physical motion | Audio result |
|---|---|
| Scan forward | Plays forward |
| Scan backward | Plays in reverse |
| Scan fast | Audio speeds up |
| Scan slow | Audio slows down |
| Hold still | Silence |
| Spin on turntable | Continuous playback |
| DJ scratch | Real-time audio scrubbing |

This applies to both flat codes and spinning discs.
On a flat code your hand is the motor.
On a disc the turntable is the motor.
Both follow the same principle.

### Two reading modes

**Static mode** — scan once, play from start to end.
Camera and code are both stationary. Full audio plays automatically.
Best for: casual listening, sharing, discovery.

**Dynamic mode** — continuous real-time reading.
Physical motion maps directly to audio timeline position.
Best for: Digilog Disc, interactive stickers, DJ performance.

It encodes compressed audio into a printable visual pattern — a grid of colored dots — that can be scanned by any camera and played back without internet, servers, or proprietary software.

It is designed to be:
- **Physical** — printed on paper, stickers, cards, posters, skin, walls, anything
- **Offline** — no URL, no server, no internet required, ever
- **Gracefully degrading** — better camera and larger print = better audio quality, like vinyl
- **Open** — the spec, the encoder, and the decoder are free for anyone to use, forever
- **Unownable** — no company can patent, buy, or close this format

---

## The Core Idea

A Digilog code is a grid of colored dots arranged in concentric rings.

Each ring encodes a different **layer** of the audio:

```
┌─────────────────────────────┐
│  ░░░░░░░░░░░░░░░░░░░░░░░░  │  ← Ring 3: Enhancement layer 2
│  ░░ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ ░░  │  ← Ring 2: Enhancement layer 1  
│  ░░ ▒▒ ████████████ ▒▒ ░░  │  ← Ring 1: Core layer (always reads)
│  ░░ ▒▒ ████████████ ▒▒ ░░  │
│  ░░ ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒ ▒▒  │
│  ░░░░░░░░░░░░░░░░░░░░░░░░  │
└─────────────────────────────┘
```

- **Core layer (center)** — largest dots, lowest density, always readable even on bad cameras, damaged prints, or scratched stickers. Contains the essential audio at minimum quality.
- **Enhancement layer 1 (middle ring)** — medium dots. Adds warmth and mid frequencies if readable.
- **Enhancement layer 2 (outer ring)** — smallest dots, highest density. Adds full fidelity if readable.

**You get what your camera can see. Exactly like a vinyl needle.**

---

## Audio Encoding

Digilog uses **Opus** — open, patent-free, and the best performing codec at low bitrates.
Each ring carries a complete independent Opus stream at increasing quality.
This is not true scalable encoding — it is three separate encodes of the same audio.
To the listener the experience is identical to true layered encoding: you hear what your camera can see.

The codec is **swappable**. The `.dtw` header declares which codec was used.
If a better open codec emerges, it can replace Opus without changing anything else in the format.

| Parameter | Value | Notes |
|---|---|---|
| Codec | Opus | Open, patent-free, widely supported |
| Channels | Mono | Maximum efficiency |
| Sample rate | 44.1 kHz | Standard audio |
| Core stream | 6 kbps | Center ring — always readable |
| Enhancement stream 1 | 12 kbps | Middle ring — average phone |
| Enhancement stream 2 | 24 kbps | Outer ring — good camera, clean print |

### Codec field values (in .dtw header)

| Value | Codec |
|---|---|
| 0x01 | Opus (current) |
| 0x02 | Reserved for future open codec |

### Future scope — Digilog Scalable Audio (DSA)

DSA is a purpose-built open codec designed specifically for Digilog's layered physical constraints.
It is not on the current roadmap — Opus is sufficient and the format is designed to swap it out cleanly when the time is right.

The idea, preserved for future contributors:

True scalable encoding where each layer is not a separate encode but a *delta* — the difference between the previous layer and higher fidelity. Core principle: encode the skeleton first, then encode only what's missing at each enhancement level. One growing thing, not three copies.

Inspired by:
- **MPEG-4 SLS** — layered architecture concept (not the patented implementation)
- **Daala** — hierarchical encoding, organic degradation at low bitrates
- **FLAC** — frame independence, resilience to partial data loss

If DSA is ever built it must be open, patent-free, and copyleft.
It would live in a separate document: `DSA_SPEC_v1.0.md`

---

## Visual Encoding

| Parameter | Value |
|---|---|
| Color depth | 8 colors (3 bits per dot) |
| Error correction | Per-layer Reed-Solomon |
| Dot shape | Square modules |
| Min module size | 3px at print DPI |
| Finder pattern | 3 corner markers (like QR) |

---

## Print Formats — The Vinyl Analogy

Bigger format = more data = better audio. The physical size *is* the quality tier.

| Format | Size | Approx capacity | Audio duration | Vinyl equivalent |
|---|---|---|---|---|
| Micro sticker | 30×30mm | ~2 KB | ~3s | Flexi disc |
| Sticker | 50×50mm | ~4 KB | ~5s | 7" single |
| Business card | 85×55mm | ~9 KB | ~12s | 7" single |
| CD inlay | 120×120mm | ~28 KB | ~37s | 10" EP |
| Postcard | 148×105mm | ~30 KB | ~40s | 10" EP |
| A5 flyer | 210×148mm | ~60 KB | ~80s | 12" LP |
| A4 poster | 210×297mm | ~122 KB | ~160s | 12" LP |

*All figures at 300 DPI, 4px modules, 8 colors, 40% error correction overhead.*

---

## Graceful Degradation — The Analog Model

Unlike QR codes, Digilog never fully fails. It degrades gracefully:

| Camera quality | What reads | What you hear |
|---|---|---|
| Poor (old phone, far away) | Core layer only | 6 kbps — rough but recognizable |
| Average (modern phone) | Core + Enhancement 1 | 12 kbps — lo-fi cassette quality |
| Good (recent phone, close) | All layers | 24 kbps — warm, full sound |

This is intentional. A scratched sticker still plays. A worn printout still plays.  
You hear what the physical object can give you — no more, no less.

---

## File Format — .dtw (Dotwave)

A `.dtw` file contains:

```
[HEADER]
  - Magic bytes: "DTW1"
  - Version: 1 byte
  - Duration: 2 bytes (seconds)
  - Layer count: 1 byte
  - Metadata length: 2 bytes

[METADATA] (optional, UTF-8 JSON)
  - artist
  - title
  - year
  - license
  - url (optional — ironic but useful)

[AUDIO LAYERS]
  - Layer 0 (core): Opus bitstream at 6 kbps
  - Layer 1 (enh1): Opus enhancement bitstream
  - Layer 2 (enh2): Opus enhancement bitstream

[CHECKSUM]
  - CRC32 per layer
```

---

## The Open Promise

Digilog is and will always be:

- Free to use, implement, and distribute
- Free to encode and decode without royalties
- Free to print, scan, share, and modify
- Protected by copyleft — any derivative format must remain open

No company may patent any part of this specification.  
This document itself serves as prior art, timestamped and published publicly.

---

## What Digilog is NOT

- Not a streaming format
- Not a DRM system
- Not owned by anyone
- Not dependent on any server, cloud, or company
- Not a replacement for high quality audio — it is a *physical* format with physical constraints, and that is a feature, not a bug

---

## Status & Roadmap

### Phase 0 — Foundation ✓
- [x] Concept defined
- [x] Layer architecture designed
- [x] Print format tiers defined
- [x] Codec selected — Opus, swappable via header flag
- [x] Spec v0.1 published (prior art established)

### Phase 1 — Prototype (current)
- [ ] Encoder (MP3 → 3x Opus streams → .dtw → printable dot grid image)
- [ ] Decoder (camera scan → layer detection → audio playback)
- [ ] Print/scan test suite (sizes, DPIs, cameras)
- [ ] GitHub repo — public, timestamped, GPL licensed

### Phase 2 — Reference Implementation
- [ ] Clean open source encoder/decoder
- [ ] PWA scanner (no install, works in browser)
- [ ] Artist tool (drag MP3, get printable file)
- [ ] Real world artist test — first song released on Digilog

### Phase 3 — Open Standard
- [ ] Community / foundation
- [ ] Formal versioned spec
- [ ] Ecosystem (sticker printers, merch integrations, etc.)

---

*Digilog was conceived in 2026 as a free physical audio format for independent artists.*  
*"Scan the groove."*

---

## Label Standard

The printed label below the dot grid shows only the human identity of the music.
No branding, no dates, no format information, no MusicBrainz IDs.

```
[artist name]     ← bold, required if known
[song title]      ← regular weight, required if known
```

**Rules:**
- If both are unknown → no label at all. White label aesthetic — intentional, valid.
- If only artist is known → artist only, no empty title line
- If only title is known → title only
- No date, no genre, no genre, no wordmark, no URL on the label
- MusicBrainz IDs and all other metadata live inside the `.dtw` file only — invisible, for machines

The dots are the format. The label is just for humans.

---

## Metadata Convention

All metadata is embedded inside the `.dtw` file as a UTF-8 JSON blob.
Every field is optional. The audio plays regardless of what metadata is present.

### Tiers

**Tier 1 — Anonymous**
No metadata at all. Completely valid. The white label.

**Tier 2 — Self-reported**
Artist types their name and song title into the encoder. No database needed.
Works for any independent artist, anywhere, without registration.

**Tier 3 — MusicBrainz linked**
Full verified identity using open MusicBrainz IDs.
For artists already in the MusicBrainz database.
Adds verifiability and links to the open music ecosystem.
Not required. Never required.

### MusicBrainz fields (all optional)

| Field | Description | Example |
|---|---|---|
| `title`           | Track title | `Guerrero` |
| `artist`          | Artist name | `Sidronio` |
| `album`           | Album name | `A E I O U` |
| `year`            | Release year | `2009` |
| `genre`           | Genre | `Rock` |
| `track`           | Track number | `1` |
| `composer`        | Composer / songwriter | `Diego Aguilar Martínez-López` |
| `bpm`             | Tempo in BPM | `120` |
| `isrc`            | ISRC recording ID | `USRC12345678` |
| `license`         | Rights statement | `All rights reserved` |
| `mb_recording_id` | MusicBrainz recording ID | `a49b4286-aed8-4f3d-af97-6f89400c31a2` |
| `mb_artist_id`    | MusicBrainz artist ID | `7b315db2-d7e0-43f6-ad55-ce382f9f91ef` |
| `mb_release_id`   | MusicBrainz release ID | `c6a67e48-60b1-4d72-bde0-ccc45ce07ec5` |

MusicBrainz is an open, free, community-maintained music database at musicbrainz.org.
Artists do not need to be in MusicBrainz for Digilog to work.

---

## Calibration Strip

Every Digilog code includes a calibration strip — a row of known reference colors printed at a fixed position. The scanner uses this strip to measure and correct for color drift introduced by printers and cameras.

### Purpose

Different printers reproduce colors differently. Different cameras read colors differently. Without calibration, color decoding is unreliable across devices.

The calibration strip makes every Digilog code self-calibrating — the scanner measures the actual drift for that specific print/camera combination and corrects accordingly. Analogous to white balance in photography.

### Position

```
┌─────────────────────────────┐
│                             │
│       dot grid (data)       │
│                             │
├─────────────────────────────┤  ← calibration strip (4 modules tall)
│ ░ █ ▒ ▓ ▒ ░ █ ░ █ ▒ ▓ ▒  │  ← 8 colors repeating full width
└─────────────────────────────┘
│     label (artist / title)  │
```

- Location: immediately below the last data row
- Height: 4 modules
- Width: full grid width
- Content: all 8 reference colors repeating left to right

### Reference Colors

These are the canonical RGB values defined by the Digilog spec. Any deviation from these values in a scan indicates drift that must be corrected.

| Index | Name    | R   | G   | B   |
|-------|---------|-----|-----|-----|
| 0     | Black   | 0   | 0   | 0   |
| 1     | White   | 255 | 255 | 255 |
| 2     | Red     | 220 | 50  | 50  |
| 3     | Green   | 50  | 180 | 50  |
| 4     | Blue    | 50  | 50  | 220 |
| 5     | Yellow  | 220 | 180 | 50  |
| 6     | Purple  | 180 | 50  | 220 |
| 7     | Cyan    | 50  | 200 | 200 |

### Calibration Algorithm

1. Locate the calibration strip (fixed position, below last data row)
2. For each of the 8 colors, average all module samples of that color in the strip
3. Calculate drift per color: `drift[i] = scanned_rgb[i] - reference_rgb[i]`
4. For each data module, find nearest reference color using uncorrected distance
5. Apply correction: `corrected_rgb = scanned_rgb - drift[nearest_color]`
6. Re-classify the corrected module to its final color index

### Decoder behavior

- If calibration strip is present and readable: use full calibration
- If calibration strip is partially readable: use partial calibration for available colors
- If calibration strip is unreadable: fall back to tolerance-based nearest-color matching

The strip degrades gracefully — partial calibration is better than none.

---

## Encoding Modes

The `.dtw` header contains an encoding mode field that defines how dots are rendered and read. This allows the format to evolve without breaking backward compatibility.

| Mode | Value | Name | Status |
|---|---|---|---|
| Discrete | `0x01` | Hard-edged colored squares | Current — v0.1 |
| Gradient | `0x02` | Soft dots with gradient transitions | Future — v2.0 |

---

### Mode 0x01 — Discrete encoding (current)

Hard-edged square modules. 8 colors. 3 bits per module.
The scanner reads the center pixel of each module and classifies it to the nearest reference color.

Robust, forgiving, works on any camera and printer.
Best for flat surfaces scanned once — stickers, cards, posters, walls.

---

### Mode 0x02 — Gradient encoding (future)

Soft dots with controlled gradient transitions between neighboring modules.
The transition zone between two adjacent dots encodes additional data beyond the dots themselves.

**Core principle:** the blend between two dots is not noise — it is signal.
The transition carries information about the relationship between neighbors,
increasing effective capacity without increasing physical dot density.

**Capacity gain:** estimated 25–100% more data in the same physical space,
depending on transition resolution and calibration accuracy.

**Designed for motion:** the natural blur of a spinning Digilog Disc
enhances gradient reading rather than degrading it.
Motion is signal, not noise.

**Aesthetic:** soft, organic, CRT-like. Dots bleed into each other
like phosphor on a screen or ink on textured paper.
Closer to analog than Mode 1.

**Requirements:**
- Enhanced calibration strip (gradient reference patches in addition to flat color patches)
- Higher precision camera (most modern phones qualify)
- Controlled print quality (professional or high-quality inkjet recommended)

**Backward compatibility:**
A Mode 0x01 scanner encountering a Mode 0x02 code will read the dot centers
and ignore transition zones — degraded but functional.
A Mode 0x02 scanner reads both modes natively.

---

## The Digilog Disc

A circular printed disc designed to spin on a standard turntable (33 or 45 RPM).
A phone camera mounted on a 3D-printed rig reads the dots as they rotate past.
Music plays continuously as the disc spins.

### Disc geometry

```
         outer ring  — layer 2 (24 kbps, densest dots)
       middle ring   — layer 1 (12 kbps)
     inner ring      — layer 0 (6 kbps, core, always readable)
   timing track      — clock marks for rotation speed detection
 center hole         — standard turntable spindle
```

### How it works

1. Disc spins on turntable at constant speed
2. Phone camera reads a radial slice of the disc as it rotates
3. Timing track on the outer edge measures exact rotation speed
4. Each full rotation = one complete pass of all data rings
5. Audio reconstructs and plays continuously in real time
6. Quality degrades gracefully inward — outer rings = best, inner = always readable

### The vinyl analogy — made literal

| Vinyl | Digilog Disc |
|---|---|
| Groove depth = audio data | Dot color = audio data |
| Needle reads groove | Camera reads dots |
| Record wear = degraded sound | Print wear = lower layer fallback |
| Turntable speed = playback rate | Rotation speed = data read rate |
| 12" LP = full album | Large disc = longer audio |
| 7" single = short track | Small disc = short track |

### 3D printed rig

An open-source phone mount designed to hold any phone at the correct
angle and distance above the spinning disc.
Design files will be published at github.com/pisdronio/digilog-spec.

**Rig specifications:**
- Fixed focal distance: optimized per disc diameter
- Camera angle: perpendicular to disc surface ±5°
- Compatible with: standard 12" and 7" turntable sizes
- Material: any FDM-printable filament (PLA recommended)
- Phone compatibility: universal clamp, fits any phone

### Disc formats

| Disc size | Equivalent | Approx audio capacity |
|---|---|---|
| 7" (18cm) | 7" single | ~30–60 seconds |
| 10" (25cm) | 10" EP | ~2–3 minutes |
| 12" (30cm) | 12" LP | ~5–8 minutes |

*Capacity depends on encoding mode, dot density, and number of rings.*
*Mode 0x02 gradient encoding significantly increases capacity per ring.*
