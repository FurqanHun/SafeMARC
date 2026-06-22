import argparse
import sys
from typing import List

from src.core.batch_processor import BatchProcessor
from src.core.scanner import SafeScanner

def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SafeMARC - Redact sensitive information from documents.")
    
    parser.add_argument("-i", "--input", type=str, required=True,
                        help="Path to a file or directory for processing.")
    
    parser.add_argument("-o", "--output-dir", type=str, default=None,
                        help="Path to the output directory. If not provided, it will create a folder alongside the original.")
    
    parser.add_argument("--use-suffix", action="store_true",
                        help="Append '_safemarc_redacted' to the original file name instead of using a separate folder.")
    
    parser.add_argument("--faces", action="store_true",
                        help="Enable face redaction (enabled by default if no flags provided).")
                        
    parser.add_argument("--redact-body", action="store_true",
                        help="Enable full body redaction instead of just faces.")
    
    parser.add_argument("--text", action="store_true",
                        help="Enable text redaction.")
    
    return parser.parse_args(args)

def main(args: List[str] = None):
    if args is None:
        args = sys.argv[1:]
        
    parsed_args = parse_args(args)
    
    # Configure detectors.
    enable_faces = parsed_args.faces
    enable_text = parsed_args.text
    enable_body = parsed_args.redact_body
    
    if not enable_faces and not enable_text and not enable_body:
        enable_faces = True
        
    vision_mode = "bodies" if enable_body else "faces"
        
    scanner = SafeScanner(vision_mode=vision_mode) 
    processor = BatchProcessor(scanner)
    
    print(f"Starting SafeMARC batch processing for: {parsed_args.input}")
    
    for file_path, success, msg in processor.process(
        input_path=parsed_args.input, 
        output_dir=parsed_args.output_dir, 
        use_suffix=parsed_args.use_suffix
    ):
        status = "✅" if success else "❌"
        print(f"{status} [{file_path}] -> {msg}")

if __name__ == "__main__":
    main()
