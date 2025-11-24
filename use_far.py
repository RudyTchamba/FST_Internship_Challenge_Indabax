import pynini
import argparse
import sys
from normalization import normalize_sentence

def load_fst_from_far(far_path, fst_name):
    """Loads a specific FST from a FAR file."""
    try:
        reader = pynini.Far(far_path, mode="r")
        while not reader.done():
            if reader.get_key() == fst_name:
                return reader.get_fst()
            reader.next()
        print(f"Error: FST '{fst_name}' not found in {far_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading FAR file: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Normalize text using a compiled FAR file.")
    parser.add_argument("text", type=str, help="The sentence to normalize")
    parser.add_argument("--far", type=str, default="normalization.far", help="Path to the .far file")
    parser.add_argument("--fst_name", type=str, default="number_normalizer", help="Name of the FST inside the FAR file")
    
    args = parser.parse_args()
    
    print(f"Loading FST '{args.fst_name}' from '{args.far}'...")
    num_fst = load_fst_from_far(args.far, args.fst_name)
    
    print(f"Normalizing: \"{args.text}\"")
    normalized_text = normalize_sentence(args.text, num_fst)
    
    print("-" * 40)
    print(f"Result: {normalized_text}")
    print("-" * 40)

if __name__ == "__main__":
    main()
