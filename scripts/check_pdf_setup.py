#!/usr/bin/env python3
"""
Check PDF generation setup.

Verifies that pdflatex is installed and can generate PDFs.
"""

import subprocess
import sys
from pathlib import Path

def check_pdflatex():
    """Check if pdflatex is installed."""
    try:
        result = subprocess.run(
            ["pdflatex", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✓ pdflatex is installed")
            print(f"  Version: {result.stdout.decode().split()[1]}")
            return True
        else:
            print("✗ pdflatex is not working correctly")
            return False
    except FileNotFoundError:
        print("✗ pdflatex is not installed")
        print("\nTo install pdflatex:")
        print("  macOS: brew install --cask mactex")
        print("  Ubuntu/Debian: sudo apt-get install texlive-latex-base texlive-latex-extra")
        print("  Jetson Nano: sudo apt-get install texlive-latex-base texlive-latex-extra")
        return False
    except Exception as e:
        print(f"✗ Error checking pdflatex: {e}")
        return False

def test_pdf_generation():
    """Test PDF generation with a simple LaTeX file."""
    test_tex = r"""
\documentclass[11pt,a4paper]{article}
\usepackage[margin=0.6in]{geometry}
\begin{document}
\title{Test PDF Generation}
\author{Job Search Pipeline}
\maketitle
This is a test PDF to verify LaTeX compilation works.
\end{document}
"""
    
    test_dir = Path("data/resumes")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_pdf.tex"
    
    try:
        # Write test file
        test_file.write_text(test_tex)
        
        # Compile
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", 
             "-output-directory", str(test_dir),
             str(test_file)],
            capture_output=True,
            timeout=30
        )
        
        pdf_file = test_file.with_suffix(".pdf")
        if pdf_file.exists():
            print("✓ PDF generation test successful")
            print(f"  Test PDF created: {pdf_file}")
            
            # Cleanup
            for ext in [".aux", ".log", ".out", ".tex"]:
                aux = test_file.with_suffix(ext)
                if aux.exists():
                    aux.unlink()
            
            return True
        else:
            print("✗ PDF generation test failed")
            print(f"  Error: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"✗ Error during PDF test: {e}")
        return False

if __name__ == "__main__":
    print("Checking PDF generation setup...\n")
    
    has_pdflatex = check_pdflatex()
    
    if has_pdflatex:
        print()
        test_pdf_generation()
    
    print("\n" + "="*50)
    if has_pdflatex:
        print("PDF generation is ready!")
    else:
        print("Please install pdflatex to enable PDF resume generation.")
        print("Resume generation will still work, but only .tex files will be created.")
        sys.exit(1)
