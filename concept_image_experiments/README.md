# Concept Image Extraction Experiments

This project tests 3 different approaches to extract content from product concept images.

## Experiments

### Experiment 1: Multimodal LLM Only (gpt-4o)
- **Method**: Direct image → gpt-4o → Text output
- **No preprocessing**: Uses OpenAI's multimodal capabilities directly
- **Best for**: Quick, comprehensive analysis with integrated text + visual understanding

### Experiment 2: OCR + LLM
- **Method**: Image → Tesseract OCR → gpt-4o → Text output
- **Text-focused**: Extracts text first, then enhances with LLM
- **Best for**: When text accuracy is critical, visual features less important

### Experiment 3: OCR + Vision Embeddings
- **Method**: Image → [Tesseract OCR + Vision Model] → gpt-4o Synthesis
- **Comprehensive**: Combines text extraction with visual feature analysis
- **Best for**: Marketing insights, positioning analysis, distinguishing lifestyle vs product imagery

## Setup

### 1. Install Python Dependencies
```bash
pip install pillow pytesseract openai
```

### 2. Install Tesseract OCR (Required for Experiments 2 & 3)

#### Windows:
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to default location (usually `C:\Program Files\Tesseract-OCR`)
3. Add to PATH or update `pytesseract.pytesseract.tesseract_cmd` in experiment scripts

#### Mac:
```bash
brew install tesseract
```

#### Linux:
```bash
sudo apt-get install tesseract-ocr
```

### 3. Set OpenAI API Key
```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
```

## Running Experiments

### Run All Experiments:
```bash
python run_all_experiments.py
```

### Run Individual Experiments:
```bash
python experiment_1_multimodal_llm.py
python experiment_2_ocr_llm.py
python experiment_3_ocr_vision_embedding.py
```

## Test Images

The experiments run on 3 selected Soap & Glory product images:
1. `Witty Optimist_Jan24.Girls Night Out cool aid.jpg` - Jelly cream with lifestyle imagery
2. `Witty Optimist_FY25.S&G Be Me Body Sprays.JPG` - Body sprays
3. `Witty Optimist_Jan24.Mission Possible Body Lotion.jpg` - Body lotion

## Output

All results are saved to `concept_image_experiments/results/`:
- `exp1_multimodal_[image_name].txt` - Experiment 1 outputs
- `exp2_ocr_llm_[image_name].txt` - Experiment 2 outputs
- `exp3_ocr_vision_[image_name].txt` - Experiment 3 outputs
- `experiment_comparison_summary.txt` - Summary and recommendations

## Project Structure

```
concept_image_experiments/
├── experiment_config.py              # Configuration and paths
├── experiment_1_multimodal_llm.py    # Experiment 1 implementation
├── experiment_2_ocr_llm.py           # Experiment 2 implementation
├── experiment_3_ocr_vision_embedding.py  # Experiment 3 implementation
├── run_all_experiments.py            # Master runner script
├── README.md                         # This file
└── results/                          # Output directory
    ├── exp1_multimodal_*.txt
    ├── exp2_ocr_llm_*.txt
    ├── exp3_ocr_vision_*.txt
    └── experiment_comparison_summary.txt
```

## Key Differences

| Feature | Exp 1: Multimodal LLM | Exp 2: OCR + LLM | Exp 3: OCR + Vision |
|---------|----------------------|------------------|---------------------|
| Text Extraction | Native LLM | Tesseract OCR | Tesseract OCR |
| Visual Analysis | Integrated | None | Separate Vision Model |
| Color Analysis | ✓ | ✗ | ✓ |
| Design Style | ✓ | ✗ | ✓ |
| Lifestyle vs Product | ✓ | ✗ | ✓ |
| Badges/Labels | ✓ | ✗ | ✓ |
| API Calls | 1 | 1 | 3 |
| Cost | $ | $ | $$$ |
| Speed | Fast | Fast | Slower |

## Recommendations

**Use Experiment 1** when:
- You need quick, comprehensive analysis
- Text is clearly readable
- Cost and speed are priorities

**Use Experiment 2** when:
- Text extraction accuracy is critical
- You only need text content
- Visual features are not important

**Use Experiment 3** when:
- You need detailed visual analysis
- Marketing positioning insights are important
- You want explicit separation of text and visual signals
- Comprehensive analysis justifies higher cost

## Troubleshooting

### Tesseract not found error:
If you get `TesseractNotFoundError`, you need to:
1. Install Tesseract OCR (see Setup section)
2. Add Tesseract to your PATH, or
3. Update the script to point to Tesseract location:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### OpenAI API errors:
- Ensure `OPENAI_API_KEY` environment variable is set
- Check your API key has credits
- Verify you have access to gpt-4o model

## Notes

- Experiment 1 can run without Tesseract (multimodal only)
- Experiments 2 & 3 require Tesseract installation
- All experiments require OpenAI API key with gpt-4o access
