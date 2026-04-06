# Digilog Format Specification
## Version 0.1 — First Draft
**Status:** Working draft  
**License:** GPL v3 — free forever, open forever  
**File extension:** `.dtw` (dotwave)  
**The verb:** "scan the groove"

---

## What is Digilog?

Digilog is a free, open, physical audio format.

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
