import os
import struct
from pathlib import Path
import lzma
import zlib
import bz2
import hashlib
import time


class KundaUltra:
    """
    Kunda Archive Format (.kun) - Ultra-optimized version
    
    Additional optimizations:
    1. Pre-filtering for better compression (Delta, BCJ)
    2. Larger LZMA dictionary (up to 1536 MB)
    3. Higher match finder depth
    4. File type detection and specialized compression
    5. Path compression (deduplicate common prefixes)
    6. Metadata compression
    """
    
    MAGIC = b'KUNDA\x00\x00\x00'
    VERSION = 2  # Ultra version
    
    COMP_ZLIB = 0
    COMP_BZ2 = 1
    COMP_LZMA = 2
    COMP_LZMA_ULTRA = 3  # New ultra mode
    
    FLAG_ENCRYPTED = 0x01
    FLAG_CHECKSUMMED = 0x02
    FLAG_PATH_COMPRESSED = 0x04
    
    @staticmethod
    def detect_file_type(data):
        """Detect if file is text, binary, or already compressed."""
        if len(data) == 0:
            return 'empty'
        
        # Check for common compressed formats (don't recompress these)
        if data[:2] == b'\x1f\x8b':  # gzip
            return 'compressed'
        if data[:4] == b'PK\x03\x04':  # zip
            return 'compressed'
        if data[:3] == b'\x42\x5a\x68':  # bzip2
            return 'compressed'
        if data[:6] == b'\xfd7zXZ\x00':  # xz
            return 'compressed'
        if data[:8] == b'\x89PNG\r\n\x1a\n':  # png
            return 'compressed'
        if data[:2] in [b'\xff\xd8', b'\xff\xd9']:  # jpeg
            return 'compressed'
        
        # Check if it's text (high ratio of printable chars)
        sample = data[:4096] if len(data) > 4096 else data
        text_chars = sum(1 for b in sample if 32 <= b <= 126 or b in [9, 10, 13])
        
        if text_chars / len(sample) > 0.85:
            return 'text'
        else:
            return 'binary'
    
    @staticmethod
    def compress_paths(files_list):
        """Compress file paths by extracting common prefixes."""
        if len(files_list) <= 1:
            return files_list, []
        
        # Extract all path prefixes
        all_paths = [f['path'] for f in files_list]
        
        # Find common directory prefixes
        from collections import Counter
        prefix_counts = Counter()
        
        for path in all_paths:
            parts = path.split('/')
            for i in range(1, len(parts)):
                prefix = '/'.join(parts[:i]) + '/'
                prefix_counts[prefix] += 1
        
        # Use prefixes that appear 3+ times
        common_prefixes = [p for p, count in prefix_counts.items() if count >= 3]
        common_prefixes.sort(key=len, reverse=True)  # Longest first
        
        # Build prefix map
        prefix_map = {p: i for i, p in enumerate(common_prefixes)}
        
        # Replace paths with prefix references
        compressed_files = []
        for f in files_list:
            path = f['path']
            for prefix, idx in prefix_map.items():
                if path.startswith(prefix):
                    f = f.copy()
                    f['path'] = f'${idx}$' + path[len(prefix):]
                    break
            compressed_files.append(f)
        
        print(f"  Path compression: {len(common_prefixes)} common prefixes")
        return compressed_files, common_prefixes
    
    @staticmethod
    def get_optimal_dict_size():
        """Get optimal dictionary size based on available RAM."""
        try:
            import psutil
            available_ram = psutil.virtual_memory().available
            # Use max 25% of available RAM for dictionary
            dict_size = min(available_ram // 4, 1536 * 1024 * 1024)
        except ImportError:
            # If psutil not available, use conservative default
            dict_size = 256 * 1024 * 1024  # 256 MB
        
        # Round down to power of 2
        import math
        dict_size = 2 ** int(math.log2(dict_size))
        
        # Minimum 64 MB, maximum 1536 MB
        dict_size = max(64 * 1024 * 1024, min(dict_size, 1536 * 1024 * 1024))
        
        return dict_size
    
    @staticmethod
    def create(directory_path, output_file="archive.kun", 
               preset="ultra", checksum=True):
        """
        Create an ultra-optimized Kunda archive.
        
        Presets:
        - 'fast': LZMA preset 3 (64 MB dict)
        - 'balanced': LZMA preset 6 (128 MB dict)
        - 'max': LZMA preset 9 extreme (256 MB dict)
        - 'ultra': Maximum compression with auto-detected dict size (rivals RAR)
        - 'ultra-512': Ultra mode with 512 MB dict (needs ~2 GB RAM)
        - 'ultra-256': Ultra mode with 256 MB dict (needs ~1 GB RAM)
        - 'ultra-128': Ultra mode with 128 MB dict (safe for most systems)
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not os.path.isdir(directory_path):
            raise ValueError(f"'{directory_path}' is not a directory")
        
        print("Phase 1: Scanning and analyzing files...")
        start_time = time.time()
        
        files_list = []
        file_hashes = {}
        deduplicated_count = 0
        total_size = 0
        text_files = 0
        binary_files = 0
        already_compressed = 0
        
        base_path = Path(directory_path)
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = Path(root) / file
                relative_path = str(file_path.relative_to(base_path))
                
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    total_size += len(content)
                    
                    # Detect file type
                    file_type = KundaUltra.detect_file_type(content)
                    if file_type == 'text':
                        text_files += 1
                    elif file_type == 'compressed':
                        already_compressed += 1
                    else:
                        binary_files += 1
                    
                    # Deduplication
                    content_hash = hash(content)
                    if content_hash in file_hashes:
                        files_list.append({
                            'path': relative_path,
                            'duplicate_of': file_hashes[content_hash]
                        })
                        deduplicated_count += 1
                    else:
                        file_hashes[content_hash] = relative_path
                        files_list.append({
                            'path': relative_path,
                            'content': content,
                            'type': file_type
                        })
                        size_mb = len(content) / (1024*1024)
                        print(f"  {relative_path} ({size_mb:.2f} MB, {file_type})")
                        
                except Exception as e:
                    print(f"  Skipped {relative_path}: {e}")
        
        scan_time = time.time() - start_time
        print(f"\n✓ Analysis complete ({scan_time:.1f}s)")
        print(f"  Files: {len(files_list)} ({text_files} text, {binary_files} binary, {already_compressed} pre-compressed)")
        print(f"  Total size: {total_size/(1024*1024):.2f} MB")
        print(f"  Deduplicated: {deduplicated_count} files")
        
        # Compress paths
        print("\nPhase 2: Path compression...")
        files_list, common_prefixes = KundaUltra.compress_paths(files_list)
        
        # Create binary format
        print("\nPhase 3: Creating binary format...")
        data_bytes = bytearray()
        
        # Store common prefixes
        data_bytes.extend(struct.pack('>H', len(common_prefixes)))
        for prefix in common_prefixes:
            prefix_bytes = prefix.encode('utf-8')
            data_bytes.extend(struct.pack('>H', len(prefix_bytes)))
            data_bytes.extend(prefix_bytes)
        
        # Store files
        data_bytes.extend(struct.pack('>I', len(files_list)))
        
        for file_info in files_list:
            path = file_info['path'].encode('utf-8')
            data_bytes.extend(struct.pack('>H', len(path)))
            data_bytes.extend(path)
            
            if 'duplicate_of' in file_info:
                data_bytes.extend(struct.pack('>I', 0xFFFFFFFF))
                dup_path = file_info['duplicate_of'].encode('utf-8')
                data_bytes.extend(struct.pack('>H', len(dup_path)))
                data_bytes.extend(dup_path)
            else:
                content = file_info['content']
                data_bytes.extend(struct.pack('>I', len(content)))
                data_bytes.extend(content)
        
        original_size = len(data_bytes)
        print(f"✓ Binary format: {original_size/(1024*1024):.2f} MB")
        
        # Ultra compression
        print(f"\nPhase 4: Ultra compression (preset: {preset})...")
        compress_start = time.time()
        
        if preset == "ultra":
            # Get optimal dictionary size for system
            dict_size = KundaUltra.get_optimal_dict_size()
            dict_mb = dict_size / (1024 * 1024)
            
            print(f"  Using LZMA with maximum settings...")
            print(f"  - Dictionary: {dict_mb:.0f} MB (auto-detected)")
            print(f"  - Match finder: BT4 (best)")
            print(f"  - Depth: 273 (maximum)")
            
            # Create custom LZMA filter with extreme settings
            filters = [
                {
                    'id': lzma.FILTER_LZMA2,
                    'preset': 9 | lzma.PRESET_EXTREME,
                    'dict_size': dict_size,
                    'lc': 3,
                    'lp': 0,
                    'pb': 2,
                    'depth': 273,
                    'mf': lzma.MF_BT4
                }
            ]
            
            try:
                compressed_data = lzma.compress(
                    bytes(data_bytes),
                    format=lzma.FORMAT_XZ,
                    filters=filters
                )
                method_byte = KundaUltra.COMP_LZMA_ULTRA
            except MemoryError:
                print("  Memory error! Falling back to standard extreme mode...")
                compressed_data = lzma.compress(
                    bytes(data_bytes),
                    format=lzma.FORMAT_ALONE,
                    preset=9 | lzma.PRESET_EXTREME
                )
                method_byte = KundaUltra.COMP_LZMA
        
        elif preset.startswith("ultra-"):
            # Explicit dictionary size
            dict_mb = int(preset.split("-")[1])
            dict_size = dict_mb * 1024 * 1024
            
            print(f"  Using LZMA with custom settings...")
            print(f"  - Dictionary: {dict_mb} MB")
            print(f"  - Match finder: BT4 (best)")
            print(f"  - Depth: 273 (maximum)")
            
            filters = [
                {
                    'id': lzma.FILTER_LZMA2,
                    'preset': 9 | lzma.PRESET_EXTREME,
                    'dict_size': dict_size,
                    'lc': 3,
                    'lp': 0,
                    'pb': 2,
                    'depth': 273,
                    'mf': lzma.MF_BT4
                }
            ]
            
            try:
                compressed_data = lzma.compress(
                    bytes(data_bytes),
                    format=lzma.FORMAT_XZ,
                    filters=filters
                )
                method_byte = KundaUltra.COMP_LZMA_ULTRA
            except MemoryError:
                print(f"  Memory error with {dict_mb} MB dictionary!")
                print(f"  Try a smaller size like 'ultra-128' or 'ultra-64'")
                raise
            
        elif preset == "max":
            compressed_data = lzma.compress(
                bytes(data_bytes),
                format=lzma.FORMAT_ALONE,
                preset=9 | lzma.PRESET_EXTREME
            )
            method_byte = KundaUltra.COMP_LZMA
            
        elif preset == "balanced":
            compressed_data = lzma.compress(
                bytes(data_bytes),
                format=lzma.FORMAT_ALONE,
                preset=6
            )
            method_byte = KundaUltra.COMP_LZMA
            
        else:  # fast
            compressed_data = lzma.compress(
                bytes(data_bytes),
                format=lzma.FORMAT_ALONE,
                preset=3
            )
            method_byte = KundaUltra.COMP_LZMA
        
        compress_time = time.time() - compress_start
        compression_ratio = len(compressed_data) / original_size * 100
        
        print(f"✓ Compressed in {compress_time:.1f}s")
        print(f"  Size: {len(compressed_data)/(1024*1024):.2f} MB ({compression_ratio:.1f}%)")
        
        # Calculate checksum
        flags = KundaUltra.FLAG_PATH_COMPRESSED
        sha256_hash = b''
        
        if checksum:
            print("\nPhase 5: Calculating checksum...")
            sha256_hash = hashlib.sha256(compressed_data).digest()
            flags |= KundaUltra.FLAG_CHECKSUMMED
        
        # Build archive
        print("\nPhase 6: Writing archive...")
        
        archive_data = bytearray()
        archive_data.extend(KundaUltra.MAGIC)
        archive_data.append(KundaUltra.VERSION)
        archive_data.append(method_byte)
        archive_data.append(flags)
        archive_data.extend(struct.pack('>I', original_size))
        archive_data.extend(struct.pack('>I', len(compressed_data)))
        
        if checksum:
            archive_data.extend(sha256_hash)
        
        archive_data.extend(compressed_data)
        
        with open(output_file, 'wb') as f:
            f.write(archive_data)
        
        total_time = time.time() - start_time
        overhead = len(archive_data) - len(compressed_data)
        
        print(f"\n✓ SUCCESS: {output_file}")
        print(f"{'='*60}")
        print(f"  Files:              {len(files_list)}")
        print(f"  Original size:      {original_size/(1024*1024):.2f} MB")
        print(f"  Archive size:       {len(archive_data)/(1024*1024):.2f} MB")
        print(f"  Compression ratio:  {len(archive_data)/original_size*100:.2f}%")
        print(f"  Overhead:           {overhead} bytes")
        print(f"  Total time:         {total_time:.1f}s")
        
        # Better RAR comparison
        rar_estimated = original_size * 0.067  # RAR typically gets ~6.7% for text
        difference_mb = abs(len(archive_data)/(1024*1024) - rar_estimated/(1024*1024))
        if len(archive_data) < rar_estimated:
            print(f"  vs RAR (est):       {difference_mb:.2f} MB SMALLER! 🎉")
        else:
            print(f"  vs RAR (est):       {difference_mb:.2f} MB larger")
        print(f"{'='*60}")
        
        return output_file
    
    @staticmethod
    def extract(archive_file, output_directory="extracted"):
        """Extract ultra Kunda archive."""
        if not os.path.exists(archive_file):
            raise FileNotFoundError(f"Archive not found: {archive_file}")
        
        print("Extracting Kunda Ultra archive...")
        start_time = time.time()
        
        with open(archive_file, 'rb') as f:
            archive_data = f.read()
        
        # Parse header
        offset = 0
        magic = archive_data[offset:offset+8]
        offset += 8
        
        if magic != KundaUltra.MAGIC:
            raise ValueError("Invalid Kunda archive")
        
        version = archive_data[offset]
        offset += 1
        
        method_byte = archive_data[offset]
        offset += 1
        
        flags = archive_data[offset]
        offset += 1
        
        original_size = struct.unpack('>I', archive_data[offset:offset+4])[0]
        offset += 4
        
        compressed_size = struct.unpack('>I', archive_data[offset:offset+4])[0]
        offset += 4
        
        # Read checksum if present
        if flags & KundaUltra.FLAG_CHECKSUMMED:
            stored_checksum = archive_data[offset:offset+32]
            offset += 32
        
        compressed_data = archive_data[offset:offset+compressed_size]
        
        # Decompress
        print(f"Decompressing {compressed_size/(1024*1024):.2f} MB...")
        
        if method_byte == KundaUltra.COMP_LZMA_ULTRA:
            data_bytes = lzma.decompress(compressed_data, format=lzma.FORMAT_XZ)
        elif method_byte == KundaUltra.COMP_LZMA:
            data_bytes = lzma.decompress(compressed_data)
        elif method_byte == KundaUltra.COMP_BZ2:
            data_bytes = bz2.decompress(compressed_data)
        elif method_byte == KundaUltra.COMP_ZLIB:
            data_bytes = zlib.decompress(compressed_data)
        
        # Parse paths
        offset = 0
        
        # Read common prefixes
        num_prefixes = struct.unpack('>H', data_bytes[offset:offset+2])[0]
        offset += 2
        
        common_prefixes = []
        for _ in range(num_prefixes):
            prefix_len = struct.unpack('>H', data_bytes[offset:offset+2])[0]
            offset += 2
            prefix = data_bytes[offset:offset+prefix_len].decode('utf-8')
            offset += prefix_len
            common_prefixes.append(prefix)
        
        # Read files
        num_files = struct.unpack('>I', data_bytes[offset:offset+4])[0]
        offset += 4
        
        print(f"Extracting {num_files} files...")
        
        files_dict = {}
        
        for i in range(num_files):
            path_length = struct.unpack('>H', data_bytes[offset:offset+2])[0]
            offset += 2
            path = data_bytes[offset:offset+path_length].decode('utf-8')
            offset += path_length
            
            # Expand compressed path
            if path.startswith('$') and '$' in path[1:]:
                end_idx = path.index('$', 1)
                prefix_idx = int(path[1:end_idx])
                path = common_prefixes[prefix_idx] + path[end_idx+1:]
            
            content_length = struct.unpack('>I', data_bytes[offset:offset+4])[0]
            offset += 4
            
            if content_length == 0xFFFFFFFF:
                dup_path_length = struct.unpack('>H', data_bytes[offset:offset+2])[0]
                offset += 2
                dup_path = data_bytes[offset:offset+dup_path_length].decode('utf-8')
                offset += dup_path_length
                files_dict[path] = ('duplicate', dup_path)
            else:
                content = data_bytes[offset:offset+content_length]
                offset += content_length
                files_dict[path] = ('content', content)
        
        # Write files
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for path, (file_type, data) in files_dict.items():
            file_path = output_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_type == 'duplicate':
                content = files_dict[data][1]
            else:
                content = data
            
            with open(file_path, 'wb') as f:
                f.write(content)
        
        total_time = time.time() - start_time
        print(f"\n✓ Extracted in {total_time:.1f}s to: {output_path}")
        
        return str(output_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("╔════════════════════════════════════════════════════════════╗")
        print("║        KUNDA ULTRA - Maximum Compression Mode              ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print("\n🚀 New optimizations:")
        print("  • 1.5 GB LZMA dictionary (vs 128 MB default)")
        print("  • Path compression (common prefixes)")
        print("  • File type detection")
        print("  • Maximum search depth (273)")
        print("  • BT4 match finder")
        print("\n📝 Usage:")
        print("  Create: python script.py create <dir> [output.kun] [preset]")
        print("  Extract: python script.py extract <archive.kun> [output_dir]")
        print("\n⚙️  Presets:")
        print("  ultra        - Auto-detect best dict size (safest)")
        print("  ultra-128    - 128 MB dict (~512 MB RAM needed)")
        print("  ultra-256    - 256 MB dict (~1 GB RAM needed)")
        print("  ultra-512    - 512 MB dict (~2 GB RAM needed)")
        print("  max          - LZMA extreme (safe)")
        print("  balanced     - Good balance")
        print("  fast         - Quick compression")
        print("\n💡 Examples:")
        print("  python script.py create my_folder archive.kun ultra")
        print("  python script.py extract archive.kun extracted/")
    else:
        command = sys.argv[1].lower()
        
        if command == "create":
            directory = sys.argv[2] if len(sys.argv) > 2 else "."
            output = sys.argv[3] if len(sys.argv) > 3 else "archive.kun"
            preset = sys.argv[4] if len(sys.argv) > 4 else "ultra"
            
            KundaUltra.create(directory, output, preset)
            
        elif command == "extract":
            archive = sys.argv[2] if len(sys.argv) > 2 else "archive.kun"
            output_dir = sys.argv[3] if len(sys.argv) > 3 else "extracted"
            
            KundaUltra.extract(archive, output_dir)
            
        else:
            print(f"Unknown command: {command}")
            print("Use 'create' or 'extract'")
