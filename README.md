# Text Normalization Internship Challenge - IndabaX

This repository contains a Finite-State Transducer (FST) based solution for text normalization, specifically targeting cardinal numbers, developed for the IndabaX Internship Challenge.

## Overview

The system normalizes written text containing numbers into their spoken form. It is built using the `pynini` library and supports both English and French.

**Example:**
*   Input: "I have 123 apples and $50."
*   Output: "I have one hundred and twenty three apples and fifty dollars."

## Features

*   **Cardinal Numbers (0-1000)**: Full support for standard cardinal numbers.
*   **Multilingual Support**:
    *   **English**: Default mode.
*   **Advanced Normalization**:
    *   **Large Numbers**: Intelligent handling of large numbers based on formatting.
        *   Formatted (e.g., `1,234,567`): Normalized as large cardinals (up to sextillion).
        *   Unformatted (e.g., `123456`): Normalized as digit sequences.
    *   **Decimals**: Correctly handles decimal points (e.g., `1.23` -> "one point two three").
    *   **Currency**: Supports `$`, `€`, `£` symbols with correct pluralization (e.g., `$100` -> "one hundred dollars").
*   **Performance**: Highly efficient FST compilation and execution.

## Setup

### Prerequisites
*   Python 3
*   Linux/Unix environment (recommended for Pynini)

### Installation
1.  Clone the repository.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The main script `normalization.py` handles FST compilation, testing, and evaluation.

### 1. Running Tests (Default)
Runs internal unit tests and generates the compiled grammar file (`normalization.far`).

**English:**
```bash
python3 normalization.py
```

### 2. Evaluation (WER Calculation)
Evaluates the system against a test file and calculates the Word Error Rate (WER).

**English:**
```bash
python3 normalization.py --eval
```
*Defaults to `test_cases_cardinal_en.txt`.*

**Custom File:**
```bash
python3 normalization.py --eval path/to/your/test_file.txt
```

### 3. Using the Compiled Grammar (FAR)
The system generates a `normalization.far` file. You can use the provided `use_far.py` script to normalize any arbitrary sentence using this compiled grammar.

```bash
python3 use_far.py "Your sentence here"
```

**Example:**
```bash
python3 use_far.py "The price is $9.99."
# Output: The price is nine point nine nine dollars.
```

## File Structure

*   `normalization.py`: Main source code containing the FST construction and normalization logic.
*   `use_far.py`: Utility script to demonstrate using the compiled `.far` file.
*   `requirements.txt`: Python dependencies.
*   `test_cases_cardinal_en.txt`: Test dataset for English.
*   `normalization.far`: Compiled Finite-State Archive (generated output).
*   `Report_Indabax.pdf`: Detailed project report.

## Methodology

The solution uses a hybrid approach:
1.  **Regex Tokenization**: Identifies number-like tokens (including currency and decimals) in the text.
2.  **FST Normalization**: Uses a Pynini-based FST to convert identified number tokens into words. The FST is constructed hierarchically (units -> tens -> hundreds -> thousands).
3.  **Python Logic**: Handles high-level logic for large number chunking and currency formatting.