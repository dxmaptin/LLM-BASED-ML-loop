# Multi-Model LLM Support for Demographic Estimation

## Overview

The system now supports **3 LLM providers**:
1. **OpenAI** (GPT-4o, GPT-5, o4-*)
2. **Google Gemini** (gemini-2.0-flash, gemini-1.5-pro)
3. **Anthropic Claude** (claude-3.5-sonnet, claude-3-opus, claude-3-haiku)

The model provider is automatically detected from the model name.

---

## Setup Instructions

### 1. Install Required Packages

```bash
# Activate your virtual environment first
cd c:\Users\d.zhang\Desktop\Experiments
.\venv\Scripts\activate

# Install Gemini support
pip install google-generativeai

# Install Claude support
pip install anthropic
```

### 2. Get API Keys

#### Google Gemini API Key:
1. Visit: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy your API key

#### Anthropic Claude API Key:
1. Visit: https://console.anthropic.com/
2. Sign up/login
3. Go to API Keys section
4. Create a new API key

### 3. Set Environment Variables

Add these to your environment variables (or `.env` file):

```bash
# Google Gemini
set GEMINI_API_KEY=your_gemini_api_key_here

# Anthropic Claude
set ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI (already configured)
set OPENAI_API_KEY=your_openai_api_key_here
```

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

**Windows Command Prompt:**
```cmd
set GEMINI_API_KEY=your_gemini_api_key_here
set ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

---

## Running Multi-Model Tests

### Test Script: `test_multi_models.py`

This script tests all 3 models on 2 demographics:
- **high_income_professionals** (best GPT-4o performer: R²=0.92)
- **road_to_retirement** (worst GPT-4o performer: R²=0.68)

```bash
cd c:\Users\d.zhang\Desktop\Experiments
.\venv\Scripts\python.exe test_multi_models.py
```

The script will:
1. Test GPT-4o on both demographics
2. Test Gemini 2.0 Flash on both demographics
3. Test Claude 3.5 Sonnet on both demographics
4. Generate a comparison CSV with R² and MAE metrics
5. Show which model performs best for each demographic

**Output:**
- Console: Detailed progress and results
- CSV: `experimental_result_multi_models/multi_model_comparison_summary.csv`

---

## How It Works

### Multi-Provider Architecture

The system uses a unified interface (`llm_providers.py`) that:

1. **Auto-detects provider** from model name:
   - `gemini-*` → Google Gemini API
   - `claude-*` → Anthropic Claude API
   - Everything else → OpenAI API

2. **Handles provider-specific details**:
   - Different API authentication methods
   - Different parameter names (max_tokens vs max_output_tokens)
   - Different response formats
   - Different usage/token tracking

3. **Unified response format**:
   - All providers return the same JSON structure
   - Token usage is tracked consistently
   - Errors are handled uniformly

### Modified Files

1. **`agent_estimator/common/llm_providers.py`** (NEW)
   - Multi-provider LLM client
   - Handles OpenAI, Gemini, and Claude APIs
   - Unified interface with automatic provider detection

2. **`agent_estimator/estimator_agent/estimator.py`** (MODIFIED)
   - Updated to use `call_llm_provider()` for Gemini/Claude
   - Falls back to existing `call_response_api()` for OpenAI
   - No other changes - all prompts and filters work the same

3. **`test_multi_models.py`** (NEW)
   - Test script for comparing all 3 models
   - Tests on best and worst performing demographics

4. **`consolidate_all_results.py`** (NEW)
   - Consolidates all 12 demographics' GPT-4o results into single CSV

---

## Model Names

### OpenAI Models:
- `gpt-4o` - GPT-4 Optimized (currently used, best results)
- `gpt-4` - GPT-4
- `gpt-5-preview` - GPT-5 Preview
- `o4-mini` - o4 Mini

### Google Gemini Models:
- `gemini-2.0-flash` - Gemini 2.0 Flash (recommended, fast)
- `gemini-1.5-pro` - Gemini 1.5 Pro (slower, more capable)

### Anthropic Claude Models:
- `claude-3.5-sonnet` - Claude 3.5 Sonnet (recommended, best reasoning)
- `claude-3-opus` - Claude 3 Opus (most capable, expensive)
- `claude-3-haiku` - Claude 3 Haiku (fastest, cheapest)

---

## Current Results (GPT-4o Baseline)

All 12 UK demographics tested with GPT-4o + Prompts + Filter:

| Demographic | R² | MAE | Above 0.70? |
|------------|-----|-----|-------------|
| high_income_professionals | 0.92 | 3.33% | ✅ YES |
| families_juggling_finances | 0.91 | 3.97% | ✅ YES |
| young_dependents | 0.90 | 4.27% | ✅ YES |
| mid_life_pressed_renters | 0.89 | 4.29% | ✅ YES |
| budgeting_elderly | 0.88 | 3.86% | ✅ YES |
| rising_metropolitans | 0.87 | 4.49% | ✅ YES |
| constrained_parents | 0.85 | 5.39% | ✅ YES |
| starting_out | 0.85 | 3.76% | ✅ YES |
| secure_homeowners | 0.84 | 5.28% | ✅ YES |
| older_working_families | 0.75 | 7.54% | ✅ YES |
| asset_rich_greys | 0.73 | 6.31% | ✅ YES |
| road_to_retirement | **0.68** | 7.10% | ❌ NO |

**Summary:**
- 11/12 demographics above R²=0.70 threshold ✅
- Mean R²: 0.84
- Mean MAE: 4.97%

See: `all_12_demographics_results.csv` for full results

---

## Next Steps

1. **Install packages** (google-generativeai, anthropic)
2. **Set API keys** (GEMINI_API_KEY, ANTHROPIC_API_KEY)
3. **Run test**: `python test_multi_models.py`
4. **Compare results**: Check which model performs best
5. **Optional**: Test all 12 demographics with best-performing model

---

## Questions/Troubleshooting

**Q: Do I need all 3 API keys?**
A: No. You can test with just one provider. The script will fail gracefully if an API key is missing.

**Q: Will my existing GPT-4o results be affected?**
A: No. All existing functionality is preserved. The new multi-provider support is additive only.

**Q: Can I test my own custom models?**
A: Yes. Just modify the `MODELS` list in `test_multi_models.py` with your model names. The system will auto-detect the provider.

**Q: What if I get "API key not found" errors?**
A: Make sure you've set the environment variable correctly and restarted your terminal/IDE.

**Q: Why are Gemini/Claude slower than GPT-4o?**
A: Different providers have different rate limits and latency. You can adjust this in the provider-specific code.

---

## Cost Estimates (Approximate)

Based on 10 questions × 2 demographics = 20 estimations:

- **GPT-4o**: ~20k tokens × 2 demographics = 40k tokens (~$0.20)
- **Gemini 2.0 Flash**: ~20k tokens × 2 demographics = 40k tokens (~$0.02, 10x cheaper!)
- **Claude 3.5 Sonnet**: ~20k tokens × 2 demographics = 40k tokens (~$0.15)

Note: Gemini is significantly cheaper! May be worth testing on all 12 demographics if performance is comparable.

---

## Files Reference

### New Files:
- `agent_estimator/common/llm_providers.py` - Multi-provider LLM client
- `test_multi_models.py` - Multi-model comparison test
- `consolidate_all_results.py` - Results consolidation script
- `all_12_demographics_results.csv` - GPT-4o baseline results
- `MULTI_MODEL_SETUP.md` - This file!

### Modified Files:
- `agent_estimator/estimator_agent/estimator.py` - Added multi-provider support

### Unchanged (still working):
- All demographic prompts
- Filter corrections (13 corrections)
- Extractor agent (LOO filtering)
- All existing test scripts
