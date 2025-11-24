import pynini
from pynini.lib import pynutil, utf8

def I_O_FST(input_str: str, output_str: str):
    """Creates an FST mapping input_str to output_str."""
    input_str = str(input_str)
    output_str = str(output_str)
    return pynini.cross(pynini.accep(input_str, token_type="utf8"), 
                        pynini.accep(output_str, token_type="utf8")).optimize()

def create_num_fst():
    # 0-9
    units_map = {
        "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
        "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
    }
    fst_units = pynini.union(*[I_O_FST(k, v) for k, v in units_map.items()]).optimize()

    # 10-19
    teens_map = {
        "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen",
        "14": "fourteen", "15": "fifteen", "16": "sixteen",
        "17": "seventeen", "18": "eighteen", "19": "nineteen"
    }
    fst_teens = pynini.union(*[I_O_FST(k, v) for k, v in teens_map.items()]).optimize()

    # Tens (20, 30, ... 90)
    tens_map = {
        "2": "twenty", "3": "thirty", "4": "forty", "5": "fifty",
        "6": "sixty", "7": "seventy", "8": "eighty", "9": "ninety"
    }
    # Map single digit to tens word
    fst_tens_digit = pynini.union(*[I_O_FST(k, v) for k, v in tens_map.items()]).optimize()
    
    # Exact tens: 20, 30... (digit + "0" -> word)
    fst_eat_zero = I_O_FST("0", "")
    fst_exact_tens = (fst_tens_digit + fst_eat_zero).optimize()

    # Compound tens: 21-99 (excluding exact tens)
    # digit + digit -> word + " " + word
    # e.g. 2 + 1 -> twenty + " " + one
    fst_space_hyphen = I_O_FST("", " ")
    # We need units 1-9 for the second digit
    units_no_zero_map = {k: v for k, v in units_map.items() if k != "0"}
    fst_units_no_zero = pynini.union(*[I_O_FST(k, v) for k, v in units_no_zero_map.items()]).optimize()
    
    fst_compound_tens = (fst_tens_digit + fst_space_hyphen + fst_units_no_zero).optimize()

    # 0-99
    fst_0_to_99 = pynini.union(fst_units, fst_teens, fst_exact_tens, fst_compound_tens).optimize()

    # Hundreds: 100-999
    # Format: digit + "00" -> word + " hundred"
    # Format: digit + (01..99) -> word + " hundred and " + (rest)
    
    fst_hundred_word = I_O_FST("", " hundred")
    
    # Exact hundreds: 100, 200...
    # digit + "00" -> word + " hundred"
    fst_eat_double_zero = I_O_FST("00", "")
    fst_exact_hundreds = (fst_units_no_zero + fst_hundred_word + fst_eat_double_zero).optimize()

    # Compound hundreds: 101-999
    # digit + (rest) -> word + " hundred and " + (rest_word)
    
    fst_space_and = I_O_FST("", " and ")
    
    # Case 1: 101-109, 201-209... (middle zero)
    # digit + "0" + digit(1-9)
    fst_middle_zero = I_O_FST("0", "")
    fst_hundreds_units = (fst_units_no_zero + fst_hundred_word + fst_space_and + fst_middle_zero + fst_units_no_zero).optimize()
    
    # Case 2: 110-199... (rest is 10-99)
    fst_10_to_99 = pynini.union(fst_teens, fst_exact_tens, fst_compound_tens).optimize()
    
    fst_hundreds_rest = (fst_units_no_zero + fst_hundred_word + fst_space_and + fst_10_to_99).optimize()
    
    fst_hundreds = pynini.union(fst_exact_hundreds, fst_hundreds_units, fst_hundreds_rest).optimize()

    # 1000
    fst_1000 = I_O_FST("1000", "one thousand")
    
    # Thousands (1,000 to 999,000 - exact thousands only for now)
    # Structure: (1-999) + "000" -> (word) + " thousand"
    # We need a union of all 1-999
    fst_1_to_99 = pynini.union(fst_units_no_zero, fst_teens, fst_exact_tens, fst_compound_tens).optimize()
    fst_1_to_999 = pynini.union(fst_1_to_99, fst_hundreds).optimize()
    
    fst_exact_thousands = (fst_1_to_999 + I_O_FST("000", " thousand")).optimize()

    # Final Union
    final_fst = pynini.union(fst_0_to_99, fst_hundreds, fst_1000, fst_exact_thousands).optimize()
    return final_fst

def create_digit_fst():
    """Creates an FST that normalizes digits one by one (e.g. 123 -> one two three)."""
    units_map = {
        "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
        "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"
    }
    fst_digits = pynini.union(*[I_O_FST(k, v) for k, v in units_map.items()]).optimize()
    
    # Allow sequence of digits separated by space in output
    # digit -> word
    # digit digit -> word + " " + word
    # We can just closure it.
    # But we need spaces between words.
    # Input: "123" -> Output: "one two three"
    # We can map digit to " word".
    
    fst_digit_space = pynini.union(*[I_O_FST(k, v + " ") for k, v in units_map.items()]).optimize()
    # The last one shouldn't have a space, or we strip it later.
    # Let's just map digit->word and insert spaces in between.
    # Pynini doesn't easily do "insert space between symbols" without a grammar.
    # Simpler: Map each digit to "word ", then remove trailing space.
    
    fst_digits_seq = fst_digit_space.closure().optimize()
    return fst_digits_seq

def normalize_large_number(num_str, num_fst):
    """
    Normalizes a large number with commas (e.g. 1,234,567) by splitting into chunks.
    """
    # Suffixes for powers of 1000: (none), thousand, million, billion, ...
    suffixes = ["", "thousand", "million", "billion", "trillion", "quadrillion", "quintillion", "sextillion"]
    
    # Split by comma
    parts = num_str.split(",")
    parts.reverse() # Process from units up
    
    normalized_parts = []
    
    for i, part in enumerate(parts):
        if i >= len(suffixes):
            break # Exceeds our supported range
            
        # Normalize the chunk (0-999)
        # We use the existing num_fst which handles 0-1000.
        # Note: num_fst expects "123", not "023". Remove leading zeros unless it's just "0".
        chunk_val = int(part)
        if chunk_val == 0:
            continue # Skip empty chunks (e.g. the 000 in 1,000,000)
            
        chunk_str = str(chunk_val)
        
        # Apply FST to chunk
        try:
            lattice = pynini.accep(chunk_str, token_type="utf8") @ num_fst
            if lattice.start() == pynini.NO_STATE_ID:
                chunk_norm = chunk_str # Fallback
            else:
                chunk_norm = pynini.shortestpath(lattice).string("utf8")
        except:
            chunk_norm = chunk_str
            
        # Add suffix
        suffix = suffixes[i]
        if suffix:
            # Check if we need a comma? User example: "One quadrillion, two hundred..."
            # We'll add comma after the chunk if it's not the first processed (which is the last in the sentence).
            # Actually, let's construct the list and join with ", ".
            if i > 0:
                chunk_norm += " " + suffix
        
        normalized_parts.append(chunk_norm)
        
    # Reverse back to get high order first
    normalized_parts.reverse()
    
    # Join with ", "
    result = ", ".join(normalized_parts)
    return result

def normalize_sentence(text, num_fst):
    import re
    
    # Create digit FST on the fly or pass it in? 
    # Better to pass it in, but for now let's create it here to avoid changing main signature too much
    # or just cache it.
    # Ideally we should pass it. Let's modify main to create it and pass it?
    # Or just create it once here (global/cached).
    # For simplicity/efficiency in this script, let's just create it. It's small.
    digit_fst = create_digit_fst()
    
    def replace_func(match):
        original_str = match.group(0)
        clean_str = original_str.replace(",", "")
        
        # Handle negative
        is_negative = False
        if clean_str.startswith("-"):
            is_negative = True
            clean_str = clean_str[1:]
            original_str_positive = original_str.lstrip("-")
        else:
            original_str_positive = original_str
            
        # Logic:
        # 1. If it has commas: Treat as Large Cardinal (chunked).
        # 2. If no commas:
        #    a. If <= 1000: Treat as Standard Cardinal (0-1000 FST).
        #    b. If > 1000: Treat as Digit Sequence.
        
        if "," in original_str_positive:
            # Case 1: Large Cardinal
            res = normalize_large_number(original_str_positive, num_fst)
        else:
            # Case 2: No commas
            try:
                val = int(clean_str)
            except:
                return original_str # Should not happen due to regex
                
            if val <= 1000:
                # Case 2a: Standard Cardinal
                try:
                    lattice = pynini.accep(clean_str, token_type="utf8") @ num_fst
                    if lattice.start() == pynini.NO_STATE_ID:
                        res = clean_str
                    else:
                        res = pynini.shortestpath(lattice).string("utf8")
                except:
                    res = clean_str
            else:
                # Case 2b: Digit Sequence
                try:
                    lattice = pynini.accep(clean_str, token_type="utf8") @ digit_fst
                    if lattice.start() == pynini.NO_STATE_ID:
                        res = clean_str
                    else:
                        res = pynini.shortestpath(lattice).string("utf8")
                        res = res.strip() # Remove trailing space
                except:
                    res = clean_str
                    
        if is_negative:
            res = "minus " + res
            
        # Capitalize first letter if requested? User example "One quadrillion". 
        # But usually normalization is lowercase. The user's example had "One". 
        # Let's stick to lowercase for consistency unless it's start of sentence, which we don't know.
        # Actually, user example: "1,234... -> One quadrillion...". 
        # But "1234... -> one two three...".
        # I will keep it lowercase to match the rest of the system.
        
        return res

    # Regex to find numbers:
    # (?<!\S) : Lookbehind
    # -? : optional negative
    # \d+ : digits
    # (?:,\d{3})* : optional comma groups
    regex = r'(?<!\S)-?\d+(?:,\d{3})*\b'
    
    new_text = re.sub(regex, replace_func, text)
    return new_text

def calculate_wer(reference, hypothesis):
    """
    Calculate Word Error Rate (WER).
    WER = (S + D + I) / N
    """
    r = reference.split()
    h = hypothesis.split()
    
    # Build the matrix
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j
        
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i-1] == h[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                substitution = d[i-1][j-1] + 1
                insertion = d[i][j-1] + 1
                deletion = d[i-1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)
                
    return d[len(r)][len(h)] / len(r) if len(r) > 0 else 0

def evaluate_file(filepath, num_fst):
    print(f"\nEvaluating on {filepath}...")
    print(f"{'Original':<30} | {'Normalized':<40} | {'Expected':<40} | {'WER':<5}")
    print("-" * 125)
    
    total_wer = 0
    count = 0
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line or '~' not in line:
            continue
            
        parts = line.split('~')
        original = parts[0]
        expected = parts[1]
        
        # Normalize
        normalized = normalize_sentence(original, num_fst)
        
        # Calculate WER
        wer = calculate_wer(expected, normalized)
        total_wer += wer
        count += 1
        
        print(f"{original:<30} | {normalized:<40} | {expected:<40} | {wer:.2f}")
        
    avg_wer = total_wer / count if count > 0 else 0
    print("-" * 125)
    print(f"Average WER: {avg_wer:.4f}")

def run_tests(num_fst):
    # Test cases
    test_nums = ["0", "1", "10", "11", "20", "21", "99", "100", "101", "110", "121", "999", "1000"]
    print("--- Unit Tests ---")
    for n in test_nums:
        try:
            lattice = pynini.accep(n, token_type="utf8") @ num_fst
            if lattice.start() != pynini.NO_STATE_ID:
                res = pynini.shortestpath(lattice).string("utf8")
                print(f"{n}: {res}")
            else:
                print(f"{n}: FAILED (No match)")
        except Exception as e:
            print(f"{n}: ERROR {e}")
            
    print("\n--- Sentence Tests (with WER) ---")
    print(f"{'Original':<30} | {'Normalized':<40} | {'Expected':<40} | {'WER':<5}")
    print("-" * 125)
    
    sentences = [
        ("I have 3 dogs and 21 cats.", "I have three dogs and twenty-one cats."),
        ("The price is 100 dollars.", "The price is one hundred dollars."),
        ("It happened in 2023.", "It happened in 2023."),
        ("There are 1000 items.", "There are one thousand items.")
    ]
    
    for original, expected in sentences:
        normalized = normalize_sentence(original, num_fst)
        wer = calculate_wer(expected, normalized)
        print(f"{original:<30} | {normalized:<40} | {expected:<40} | {wer:.2f}")
    print("-" * 125)

def main():
    import argparse
    import os
    import time
    
    parser = argparse.ArgumentParser(description="Text Normalization (0-1000)")
    parser.add_argument("--eval", type=str, help="Path to test file for WER evaluation", nargs='?', const="test_cases_cardinal_en.txt")
    parser.add_argument("--test", action="store_true", help="Run internal unit and sentence tests")
    args = parser.parse_args()

    print("Compiling grammar...")
    start_time = time.time()
    num_fst = create_num_fst()
    compilation_time = time.time() - start_time
    print(f"Grammar compilation time: {compilation_time:.4f} seconds")
    
    # Run evaluation if flag is present
    if args.eval:
        # Default file if flag is present but no value
        eval_file = args.eval if args.eval != "test_cases_cardinal_en.txt" and args.eval is not None else "test_cases_cardinal_en.txt"
        
        # If args.eval is a string (filename), use it.
        eval_file = args.eval if args.eval else "test_cases_cardinal_en.txt"
        
        if os.path.exists(eval_file):
            start_runtime = time.time()
            evaluate_file(eval_file, num_fst)
            runtime = time.time() - start_runtime
            print(f"Evaluation runtime: {runtime:.4f} seconds")
        else:
            print(f"Test file '{eval_file}' not found.")
            
    # Run internal tests if --test is passed OR if no evaluation is requested (default)
    if args.test or not args.eval:
        start_runtime = time.time()
        run_tests(num_fst)
        runtime = time.time() - start_runtime
        print(f"Tests runtime: {runtime:.4f} seconds")

    # Export FAR
    try:
        writer = pynini.Far("normalization.far", mode="w")
        writer.add("number_normalizer", num_fst)
        # print("\nSuccessfully created normalization.far")
    except Exception as e:
        print(f"\nError creating FAR: {e}")

if __name__ == "__main__":
    main()
