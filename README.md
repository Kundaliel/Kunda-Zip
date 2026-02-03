# Kunda Zip - Multi-Platform Archiver

A high-performance file archiver with maximum LZMA compression, available in both C and Python.

## Project Structure

```
.
├── Makefile              # C build system
├── setup.sh              # Automated setup script
├── organize.sh           # Directory organization script
├── README.md             # This file
├── src/
│   ├── c/                # C source code
│   │   └── kunda_zip.c
│   └── python/           # Python implementations
│       ├── kunda.py      (original)
│       ├── kunda_ultra.py (optimized)
│       └── kunda_gui.py (Gui Version)
└── build/                # Compiled binaries
    └── kunda_zip         (C executable)
```

## Features

- **Ultra LZMA Compression**: Up to 1.5 GB dictionary size for maximum compression
- **Path Compression**: Deduplicates common directory prefixes
- **File Type Detection**: Automatically detects and optimizes compression for different file types
- **File Deduplication**: Automatically detects and eliminates duplicate files
- **SHA-256 Checksums**: Optional integrity verification
- **Multiple Presets**: From fast to ultra compression modes

## Requirements

### Libraries
- **liblzma** (XZ Utils) - for LZMA compression
- **OpenSSL** (libssl, libcrypto) - for SHA-256 checksums

### Quick Setup (Recommended)

**Use the automated setup script** (works on macOS and Linux):

```bash
chmod +x setup.sh
./setup.sh
```

This will:
1. Detect your OS
2. Check for dependencies
3. Install missing dependencies (with your permission)
4. Build the project automatically

### Manual Installation

If you prefer manual setup or the script doesn't work:

#### Ubuntu/Debian
```bash
sudo apt-get install liblzma-dev libssl-dev
```

### Installation on Fedora/RHEL
```bash
sudo dnf install xz-devel openssl-devel
```

### Installation on macOS
```bash
brew install xz openssl
```

## Building

### Automated Build (Recommended)

```bash
./setup.sh
```

### Manual Build Methods

#### Method 1: Auto-install dependencies then build
```bash
make install-deps  # Installs dependencies for your OS
make               # Builds the project
```

#### Method 2: Just build (if you already have dependencies)
```bash
make
```

### Advanced Build Options

#### Simple build
```bash
make
```

### Debug build
```bash
make debug
```

### Install system-wide
```bash
sudo make install
```

### Uninstall
```bash
sudo make uninstall
```

## Usage

### C Implementation (Fastest)

You can compress either a **single file** or an **entire directory**:

```bash
./build/kunda_zip create <file|directory> [output.kun] [preset]
```

**Examples:**
```bash
# Compress a single file
./build/kunda_zip create large_file.txt compressed.kun ultra

# Compress a directory with ultra compression
./build/kunda_zip create my_folder archive.kun ultra

# Compress a video file with 256 MB dictionary
./build/kunda_zip create movie.mp4 movie.kun ultra-256

# Compress a database dump with maximum compression
./build/kunda_zip create backup.sql backup.kun max

# Quick compression of a single file
./build/kunda_zip create document.pdf doc.kun fast
```

### Python Implementation

```bash
# Use the optimized Python version
python src/python/kunda_ultra.py create myfile.txt output.kun ultra

# Or the original version
python src/python/kunda.py create myfile.txt output.kun ultra
```

### GUI Version (Python)

```bash
python src/gui/kunda_gui.py
```

### Extract Archive

```bash
./build/kunda_zip extract <archive.kun> [output_directory]
```

**Examples:**
```bash
# Extract to default 'extracted' folder
./build/kunda_zip extract archive.kun

# Extract to specific directory
./build/kunda_zip extract archive.kun my_files/

# Using Python version
python src/python/kunda_ultra.py extract archive.kun extracted/
```

## Compression Presets

| Preset | Dictionary Size | RAM Usage | Speed | Compression |
|--------|----------------|-----------|-------|-------------|
| `fast` | 64 MB | ~256 MB | Fast | Good |
| `balanced` | 128 MB | ~512 MB | Medium | Better |
| `max` | 256 MB | ~1 GB | Slow | Excellent |
| `ultra` | Auto-detect | Variable | Very Slow | Maximum |
| `ultra-128` | 128 MB | ~512 MB | Very Slow | Maximum |
| `ultra-256` | 256 MB | ~1 GB | Very Slow | Maximum |
| `ultra-512` | 512 MB | ~2 GB | Very Slow | Maximum |

## Archive Format

**Header (11+ bytes):**
- Magic number: "KUNDA\x00\x00\x00" (8 bytes)
- Version: 2 (1 byte)
- Compression method (1 byte)
- Flags (1 byte)
- Original size (4 bytes, big-endian)
- Compressed size (4 bytes, big-endian)
- SHA-256 checksum (32 bytes, optional)

**Data:**
- Compressed archive data (LZMA/XZ format)

## Which Version Should I Use?

### C Version (`src/c/kunda_zip`)
**Pros:**
- ✅ 5-10x faster compression/decompression
- ✅ Lower memory usage
- ✅ Single compiled binary, no dependencies at runtime
- ✅ Best for large files and production use

**Cons:**
- ❌ Requires compilation
- ❌ Platform-specific binary

**Best for:** Production use, large files, batch processing, maximum performance

### Python Version (`src/python/kunda_ultra.py`)
**Pros:**
- ✅ No compilation needed
- ✅ Cross-platform (works anywhere Python runs)
- ✅ Easier to modify and extend
- ✅ Better error messages

**Cons:**
- ❌ Slower than C version
- ❌ Requires Python and dependencies

**Best for:** Quick tasks, development, cross-platform portability

### GUI Version (`src/gui/kunda_gui.py`)
**Best for:** Users who prefer graphical interfaces over command line

## Performance Tips

1. **Memory**: Ultra presets require significant RAM. Start with `ultra-128` if unsure.
2. **CPU**: Compression is CPU-intensive. Use `fast` or `balanced` for quick archives.
3. **File Types**: Pre-compressed files (JPEG, PNG, ZIP) won't benefit from archiving.
4. **Large Files**: Ultra mode works best with large, compressible text files.

## Use Cases

### When to Use Single File Compression

- **Large text files**: Log files, SQL dumps, CSV exports, XML data
- **Source code files**: Large concatenated codebases
- **Uncompressed media**: RAW images, WAV audio, uncompressed video
- **Virtual machine images**: Disk images, VM snapshots
- **Database backups**: Plain text database dumps

### When to Use Directory Compression

- **Project folders**: Entire codebases with dependencies
- **Document collections**: Multiple related files
- **Website backups**: Complete site structures
- **Photo albums**: Collections of images (though already compressed)

### Compression Ratios by File Type

| File Type | Typical Ratio | Notes |
|-----------|--------------|-------|
| Text files | 5-15% | Excellent compression |
| Source code | 10-20% | Very good compression |
| Log files | 3-10% | Outstanding compression |
| Already compressed | 95-100% | No benefit, skip |
| Binary executables | 40-70% | Moderate compression |
| Databases (text) | 5-15% | Excellent compression |

## Implementation Comparison

| Feature | C Version | Python Version |
|---------|-----------|----------------|
| Speed | ⚡ Fastest | Moderate |
| Memory | 💾 Lowest | Higher |
| Portability | Needs compilation | ✅ Cross-platform |
| Dependencies | Runtime: None | Python + libraries |
| Ease of Use | Binary executable | Script |
| Customization | Requires C knowledge | Easy to modify |

## Technical Details

### Optimizations
- BT4 match finder (best for compression ratio)
- Maximum search depth (273)
- Extreme preset with custom parameters
- LC=3, LP=0, PB=2 for optimal text compression

### File Type Detection
- Checks for common compressed formats (gzip, zip, PNG, JPEG, etc.)
- Analyzes text vs binary content
- Skips re-compression of already-compressed files

### Path Compression
- Extracts common directory prefixes
- Uses prefix references to reduce metadata size
- Typically saves 10-30% on path storage

## Troubleshooting

### Compilation Errors

**Error: `lzma.h: No such file or directory`**
```bash
# Install liblzma development files
sudo apt-get install liblzma-dev  # Debian/Ubuntu
sudo dnf install xz-devel          # Fedora/RHEL
```

**Error: `openssl/sha.h: No such file or directory`**
```bash
# Install OpenSSL development files
sudo apt-get install libssl-dev    # Debian/Ubuntu
sudo dnf install openssl-devel     # Fedora/RHEL
```

### Runtime Errors

**Memory allocation failed**
- Try a smaller dictionary size (e.g., `ultra-128` instead of `ultra-512`)
- Close other applications to free RAM
- Use `balanced` or `max` preset

**Cannot open directory**
- Check directory path
- Verify read permissions
- Ensure directory exists

## License

This is a C reimplementation of the Kunda Ultra archiver format.

## Contributing

Contributions welcome! Areas for improvement:
- Multi-threading support
- Solid compression (better deduplication)
- BCJ/Delta filters for executables
- Progress bars
- Resume capability for interrupted operations
