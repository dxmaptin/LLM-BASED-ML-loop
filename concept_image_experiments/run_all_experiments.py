"""
Master script to run all 3 experiments sequentially
"""
import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from experiment_1_multimodal_llm import run_experiment_1
from experiment_2_ocr_llm import run_experiment_2
from experiment_3_ocr_vision_embedding import run_experiment_3
from experiment_config import OUTPUT_DIR, TEST_IMAGES


def create_summary(exp1_results, exp2_results, exp3_results):
    """Create a comparison summary of all experiments"""
    summary_path = os.path.join(OUTPUT_DIR, "experiment_comparison_summary.txt")

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("CONCEPT IMAGE EXTRACTION EXPERIMENTS - SUMMARY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Images Tested: {len(TEST_IMAGES)}\n\n")

        f.write("TEST IMAGES:\n")
        for i, img in enumerate(TEST_IMAGES, 1):
            f.write(f"  {i}. {img}\n")
        f.write("\n" + "="*80 + "\n\n")

        f.write("EXPERIMENT OVERVIEW:\n\n")

        f.write("EXPERIMENT 1: Multimodal LLM Only (gpt-4o)\n")
        f.write("-"*80 + "\n")
        f.write("Method: Direct image → gpt-4o → Text output\n")
        f.write("Strengths:\n")
        f.write("  - No preprocessing required\n")
        f.write("  - Captures both text and visual context natively\n")
        f.write("  - Understands relationships between text and images\n")
        f.write("  - Most comprehensive single-pass analysis\n")
        f.write("Limitations:\n")
        f.write("  - Dependent on model's OCR capabilities\n")
        f.write("  - May miss small or stylized text\n")
        f.write("  - Single point of failure\n\n")

        f.write("EXPERIMENT 2: OCR + LLM\n")
        f.write("-"*80 + "\n")
        f.write("Method: Image → Tesseract OCR → gpt-4o → Text output\n")
        f.write("Strengths:\n")
        f.write("  - Specialized OCR may catch text better\n")
        f.write("  - Explicit text extraction step\n")
        f.write("  - LLM cleans up OCR errors\n")
        f.write("Limitations:\n")
        f.write("  - No visual context captured\n")
        f.write("  - Misses color, design, imagery signals\n")
        f.write("  - OCR may fail on stylized fonts\n")
        f.write("  - Loses lifestyle vs product-only distinction\n\n")

        f.write("EXPERIMENT 3: OCR + Vision Embeddings\n")
        f.write("-"*80 + "\n")
        f.write("Method: Image → [Tesseract OCR + Vision Model] → gpt-4o Synthesis\n")
        f.write("Strengths:\n")
        f.write("  - Captures text content (OCR)\n")
        f.write("  - Captures visual features (color, style, imagery type)\n")
        f.write("  - Combines both for comprehensive analysis\n")
        f.write("  - Best for marketing/positioning insights\n")
        f.write("  - Separates text from visual signals explicitly\n")
        f.write("Limitations:\n")
        f.write("  - More complex pipeline\n")
        f.write("  - Higher API costs (multiple calls)\n")
        f.write("  - Slower processing time\n\n")

        f.write("="*80 + "\n\n")

        f.write("RESULTS LOCATION:\n")
        f.write(f"All experiment outputs saved to: {OUTPUT_DIR}\n\n")

        f.write("OUTPUT FILES:\n")
        f.write("  Experiment 1: exp1_multimodal_[image_name].txt\n")
        f.write("  Experiment 2: exp2_ocr_llm_[image_name].txt\n")
        f.write("  Experiment 3: exp3_ocr_vision_[image_name].txt\n\n")

        f.write("="*80 + "\n\n")

        f.write("RECOMMENDATIONS:\n\n")

        f.write("Use EXPERIMENT 1 (Multimodal LLM) when:\n")
        f.write("  ✓ You need quick, comprehensive analysis\n")
        f.write("  ✓ Text is clearly readable in images\n")
        f.write("  ✓ You want integrated text + visual understanding\n")
        f.write("  ✓ Cost and speed are priorities\n\n")

        f.write("Use EXPERIMENT 2 (OCR + LLM) when:\n")
        f.write("  ✓ Text extraction accuracy is critical\n")
        f.write("  ✓ You only need text content\n")
        f.write("  ✓ Visual features are not important\n")
        f.write("  ✓ You want explicit OCR control\n\n")

        f.write("Use EXPERIMENT 3 (OCR + Vision Embeddings) when:\n")
        f.write("  ✓ You need detailed visual analysis (color, style, imagery type)\n")
        f.write("  ✓ Marketing positioning insights are important\n")
        f.write("  ✓ You want to distinguish lifestyle vs product-only imagery\n")
        f.write("  ✓ You need explicit separation of text and visual signals\n")
        f.write("  ✓ Comprehensive analysis justifies higher cost\n\n")

        f.write("="*80 + "\n")

    print(f"\n[OK] Summary saved to: experiment_comparison_summary.txt")
    return summary_path


def main():
    """Run all experiments"""
    print("\n" + "="*80)
    print("CONCEPT IMAGE EXTRACTION EXPERIMENTS")
    print("Testing 3 different approaches on 3 product images")
    print("="*80)

    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("\n[WARNING] OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key before running experiments")
        print("\nExample:")
        print("  set OPENAI_API_KEY=your-api-key-here  (Windows)")
        print("  export OPENAI_API_KEY=your-api-key-here  (Linux/Mac)")
        return

    try:
        # Run all experiments
        print("\n" + "="*80)
        print("Starting experiments...")
        print("="*80)

        exp1_results = run_experiment_1()
        exp2_results = run_experiment_2()
        exp3_results = run_experiment_3()

        # Create summary
        print("\n" + "="*80)
        print("Creating comparison summary...")
        print("="*80)
        create_summary(exp1_results, exp2_results, exp3_results)

        print("\n" + "="*80)
        print("ALL EXPERIMENTS COMPLETE!")
        print("="*80)
        print(f"\nResults saved to: {OUTPUT_DIR}")
        print("\nNext steps:")
        print("  1. Review individual experiment outputs")
        print("  2. Compare results across experiments")
        print("  3. Read experiment_comparison_summary.txt for recommendations")

    except Exception as e:
        print(f"\n[ERROR] Error running experiments: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
