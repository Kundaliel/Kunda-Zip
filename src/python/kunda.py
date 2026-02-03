import os
import struct
from pathlib import Path
import lzma
import zlib
import bz2
import hashlib
import time


class KunArchive:
    """
    Kunda Archive Format (.kun) - Ultra-efficient custom archive.
    
    File structure:
    [8 bytes] Magic number: "KUNDA\x00\x00\x00"
    [1 byte]  Version: 1
    [1 byte]  Compression method: 0=zlib, 1=bz2, 2=lzma
    [1 byte]  Flags: bit0=encrypted, bit1=checksummed
    [4 bytes] Original size (uncompressed)
    [4 bytes] Compressed size
    [32 bytes] SHA256 checksum (if checksummed)
    [N bytes] Compressed data
    
    Total overhead: 19 bytes (or 51 bytes with checksum)
    """
    
    MAGIC = b'KUNDA\x00\x00\x00'
    VERSION = 1
    
    # Compression methods
    COMP_ZLIB = 0
    COMP_BZ2 = 1
    COMP_LZMA = 2
    
    # Flags
    FLAG_ENCRYPTED = 0x01
    FLAG_CHECKSUMMED = 0x02
    
    @staticmethod
    def create(directory_path, output_file="archive.kun", 
               compression="lzma", preset="fast", 
               checksum=True, password=None):
        """
        Create a Kunda archive (.kun).
        
        Args:
            directory_path: Directory to archive
            output_file: Output filename (.kun = Kunda Archive)
            compression: 'zlib', 'bz2', 'lzma', or 'auto'
            preset: 'fast', 'balanced', or 'max'
            checksum: Include SHA256 checksum for integrity
            password: Optional password for encryption (not implemented yet)
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not os.path.isdir(directory_path):
            raise ValueError(f"'{directory_path}' is not a directory")
        
        print("Phase 1: Scanning directory...")
        start_time = time.time()
        
        # Collect files with deduplication
        files_list = []
        file_hashes = {}
        deduplicated_count = 0
        total_size = 0
        
        base_path = Path(directory_path)
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = Path(root) / file
                relative_path = str(file_path.relative_to(base_path))
                
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    total_size += len(content)
                    
                    # Deduplication
                    content_hash = hash(content)
                    if content_hash in file_hashes:
                        files_list.append({
                            'path': relative_path,
                            'duplicate_of': file_hashes[content_hash]
                        })
                        deduplicated_count += 1
                        print(f"  Duplicate: {relative_path}")
                    else:
                        file_hashes[content_hash] = relative_path
                        files_list.append({
                            'path': relative_path,
                            'content': content
                        })
                        size_mb = len(content) / (1024*1024)
                        print(f"  Added: {relative_path} ({size_mb:.2f} MB)")
                        
                except Exception as e:
                    print(f"  Skipped {relative_path}: {e}")
        
        scan_time = time.time() - start_time
        print(f"\n✓ Scanned {len(files_list)} files in {scan_time:.1f}s")
        print(f"  Total size: {total_size/(1024*1024):.2f} MB")
        if deduplicated_count > 0:
            print(f"  Deduplicated: {deduplicated_count} files")
        
        # Create binary format
        print("\nPhase 2: Creating binary format...")
        data_bytes = bytearray()
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
        
        # Compress
        print(f"\nPhase 3: Compressing with {compression.upper()} ({preset} preset)...")
        compress_start = time.time()
        
        if compression == "lzma":
            if preset == "fast":
                lzma_preset = 3
            elif preset == "balanced":
                lzma_preset = 6
            else:
                lzma_preset = 9 | lzma.PRESET_EXTREME
            
            compressed_data = lzma.compress(bytes(data_bytes), 
                                           format=lzma.FORMAT_ALONE,
                                           preset=lzma_preset)
            method_byte = KunArchive.COMP_LZMA
            
        elif compression == "bz2":
            compress_level = 5 if preset == "fast" else 9
            compressed_data = bz2.compress(bytes(data_bytes), compresslevel=compress_level)
            method_byte = KunArchive.COMP_BZ2
            
        elif compression == "zlib":
            compress_level = 6 if preset == "fast" else 9
            compressed_data = zlib.compress(bytes(data_bytes), level=compress_level)
            method_byte = KunArchive.COMP_ZLIB
            
        else:  # auto
            print("  Testing compression methods...")
            if original_size > 50 * 1024 * 1024:
                methods = {
                    'zlib': (zlib.compress(bytes(data_bytes), level=9), KunArchive.COMP_ZLIB),
                    'bz2': (bz2.compress(bytes(data_bytes), compresslevel=9), KunArchive.COMP_BZ2),
                }
            else:
                methods = {
                    'zlib': (zlib.compress(bytes(data_bytes), level=9), KunArchive.COMP_ZLIB),
                    'bz2': (bz2.compress(bytes(data_bytes), compresslevel=9), KunArchive.COMP_BZ2),
                    'lzma': (lzma.compress(bytes(data_bytes), preset=6), KunArchive.COMP_LZMA)
                }
            
            for name, (data, _) in methods.items():
                print(f"    {name}: {len(data)/(1024*1024):.2f} MB")
            
            best = min(methods, key=lambda k: len(methods[k][0]))
            compressed_data, method_byte = methods[best]
            print(f"  ✓ Selected: {best}")
        
        compress_time = time.time() - compress_start
        compression_ratio = len(compressed_data) / original_size * 100
        
        print(f"✓ Compressed in {compress_time:.1f}s")
        print(f"  Size: {len(compressed_data)/(1024*1024):.2f} MB ({compression_ratio:.1f}%)")
        
        # Calculate checksum if requested
        flags = 0
        sha256_hash = b''
        
        if checksum:
            print("\nPhase 4: Calculating checksum...")
            sha256_hash = hashlib.sha256(compressed_data).digest()
            flags |= UltraArchive.FLAG_CHECKSUMMED
            print(f"  SHA256: {sha256_hash.hex()}")
        
        # Build archive file
        print("\nPhase 5: Writing archive...")
        
        archive_data = bytearray()
        
        # Header
        archive_data.extend(KunArchive.MAGIC)                          # 8 bytes
        archive_data.append(KunArchive.VERSION)                        # 1 byte
        archive_data.append(method_byte)                                 # 1 byte
        archive_data.append(flags)                                       # 1 byte
        archive_data.extend(struct.pack('>I', original_size))            # 4 bytes
        archive_data.extend(struct.pack('>I', len(compressed_data)))    # 4 bytes
        
        # Checksum (if enabled)
        if checksum:
            archive_data.extend(sha256_hash)                             # 32 bytes
        
        # Compressed data
        archive_data.extend(compressed_data)
        
        # Write to file
        with open(output_file, 'wb') as f:
            f.write(archive_data)
        
        total_time = time.time() - start_time
        overhead = len(archive_data) - len(compressed_data)
        
        print(f"\n{'='*60}")
        print(f"✓ SUCCESS: {output_file}")
        print(f"{'='*60}")
        print(f"  Files:              {len(files_list)}")
        print(f"  Original size:      {original_size/(1024*1024):.2f} MB")
        print(f"  Archive size:       {len(archive_data)/(1024*1024):.2f} MB")
        print(f"  Compression ratio:  {len(archive_data)/original_size*100:.1f}%")
        print(f"  Overhead:           {overhead} bytes ({overhead/(1024):.2f} KB)")
        print(f"  Total time:         {total_time:.1f}s")
        print(f"  Savings vs PNG:     ~{(13000 - overhead)/1024:.1f} KB less overhead")
        print(f"{'='*60}")
        
        return output_file
    
    @staticmethod
    def extract(archive_file, output_directory="extracted"):
        """Extract a Kunda archive (.kun)."""
        if not os.path.exists(archive_file):
            raise FileNotFoundError(f"Archive not found: {archive_file}")
        
        print("Phase 1: Reading archive...")
        start_time = time.time()
        
        with open(archive_file, 'rb') as f:
            archive_data = f.read()
        
        print(f"  Archive size: {len(archive_data)/(1024*1024):.2f} MB")
        
        # Parse header
        offset = 0
        
        magic = archive_data[offset:offset+8]
        offset += 8
        
        if magic != KunArchive.MAGIC:
            raise ValueError("Invalid Kunda archive format")
        
        version = archive_data[offset]
        offset += 1
        
        if version != KunArchive.VERSION:
            raise ValueError(f"Unsupported version: {version}")
        
        method_byte = archive_data[offset]
        offset += 1
        
        flags = archive_data[offset]
        offset += 1
        
        original_size = struct.unpack('>I', archive_data[offset:offset+4])[0]
        offset += 4
        
        compressed_size = struct.unpack('>I', archive_data[offset:offset+4])[0]
        offset += 4
        
        # Read checksum if present
        has_checksum = bool(flags & KunArchive.FLAG_CHECKSUMMED)
        stored_checksum = None
        
        if has_checksum:
            stored_checksum = archive_data[offset:offset+32]
            offset += 32
            print(f"  Stored checksum: {stored_checksum.hex()}")
        
        method_names = {
            KunArchive.COMP_ZLIB: 'zlib',
            KunArchive.COMP_BZ2: 'bz2',
            KunArchive.COMP_LZMA: 'lzma'
        }
        compression_method = method_names.get(method_byte, 'unknown')
        
        print(f"  Method: {compression_method.upper()}")
        print(f"  Original: {original_size/(1024*1024):.2f} MB")
        print(f"  Compressed: {compressed_size/(1024*1024):.2f} MB")
        
        # Extract compressed data
        compressed_data = archive_data[offset:offset+compressed_size]
        
        # Verify checksum
        if has_checksum:
            print("\nPhase 2: Verifying checksum...")
            calculated_checksum = hashlib.sha256(compressed_data).digest()
            if calculated_checksum != stored_checksum:
                raise ValueError("Checksum mismatch! Archive may be corrupted.")
            print("  ✓ Checksum valid")
        
        # Decompress
        print(f"\nPhase 3: Decompressing {compression_method.upper()}...")
        decompress_start = time.time()
        
        if compression_method == 'zlib':
            data_bytes = zlib.decompress(compressed_data)
        elif compression_method == 'bz2':
            data_bytes = bz2.decompress(compressed_data)
        elif compression_method == 'lzma':
            data_bytes = lzma.decompress(compressed_data)
        else:
            raise ValueError(f"Unknown compression: {method_byte}")
        
        decompress_time = time.time() - decompress_start
        print(f"✓ Decompressed in {decompress_time:.1f}s")
        
        # Parse files
        print("\nPhase 4: Extracting files...")
        offset = 0
        num_files = struct.unpack('>I', data_bytes[offset:offset+4])[0]
        offset += 4
        
        print(f"  Files to extract: {num_files}")
        
        files_dict = {}
        
        for i in range(num_files):
            path_length = struct.unpack('>H', data_bytes[offset:offset+2])[0]
            offset += 2
            path = data_bytes[offset:offset+path_length].decode('utf-8')
            offset += path_length
            
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
            
            if (i + 1) % 50 == 0:
                print(f"  Parsed: {i+1}/{num_files}")
        
        # Write files
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("\nPhase 5: Writing files...")
        for i, (path, (file_type, data)) in enumerate(files_dict.items()):
            file_path = output_path / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if file_type == 'duplicate':
                content = files_dict[data][1]
            else:
                content = data
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            if (i + 1) % 50 == 0:
                print(f"  Written: {i+1}/{num_files}")
        
        total_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✓ EXTRACTION COMPLETE: {output_path}")
        print(f"{'='*60}")
        print(f"  Files extracted:    {num_files}")
        print(f"  Total time:         {total_time:.1f}s")
        print(f"{'='*60}")
        
        return str(output_path)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("╔════════════════════════════════════════════════════════════╗")
        print("║          KUNDA ARCHIVE - Ultra-Efficient Format           ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print("\n📦 File Format: .kun")
        print("🔮 Magic: KUNDA")
        print("\nOverhead comparison:")
        print("  ZIP format:      ~22 bytes + directory overhead")
        print("  TAR.XZ format:   ~1024 bytes + tar headers")
        print("  PNG format:      ~13,000 bytes")
        print("  Kunda Archive:   19 bytes (or 51 with checksum)")
        print("\n✨ Features:")
        print("  • Minimal overhead (19-51 bytes)")
        print("  • Multiple compression methods")
        print("  • File deduplication")
        print("  • Optional SHA256 checksum")
        print("  • Fast presets")
        print("\n📝 Usage:")
        print("  Create: python script.py create <dir> [output.kun] [method] [preset] [--no-checksum]")
        print("  Extract: python script.py extract <archive.kun> [output_dir]")
        print("\n💡 Examples:")
        print("  python script.py create my_folder archive.kun lzma fast")
        print("  python script.py create my_folder archive.kun auto")
        print("  python script.py create my_folder archive.kun lzma fast --no-checksum")
        print("  python script.py extract archive.kun extracted/")
        print("\n🎨 Made with Kunda magic ✨")
    else:
        command = sys.argv[1].lower()
        
        if command == "create":
            directory = sys.argv[2] if len(sys.argv) > 2 else "."
            output = sys.argv[3] if len(sys.argv) > 3 else "archive.kun"
            method = sys.argv[4] if len(sys.argv) > 4 else "lzma"
            preset = sys.argv[5] if len(sys.argv) > 5 else "fast"
            checksum = "--no-checksum" not in sys.argv
            
            KunArchive.create(directory, output, method, preset, checksum)
            
        elif command == "extract":
            archive = sys.argv[2] if len(sys.argv) > 2 else "archive.kun"
            output_dir = sys.argv[3] if len(sys.argv) > 3 else "extracted"
            
            KunArchive.extract(archive, output_dir)
            
        else:
            print(f"Unknown command: {command}")
            print("Use 'create' or 'extract'")
