# Quick Start Guide - Improved Estimator

## What Changed?

Your estimator agent now automatically:

1. ✅ **Identifies proximal toplines** - Finds exact-match quantitative data for your concepts
2. ✅ **Infers concept types** - Automatically classifies as attitude/behavior/identity
3. ✅ **Applies hard guardrails** - Prevents range compression using magnitude bands
4. ✅ **Prioritizes evidence correctly** - Proximal data always dominates over distal signals
5. ✅ **Allocates Slightly vs Strongly properly** - Based on concept type

## No Action Needed!

The system works automatically with your existing code. Just run it as before:

```python
from agent_estimator.orchestrator import run_agentic_pipeline

# Same as before - everything else is handled automatically
run_agentic_pipeline()
```

## Key Improvements to Expect

### Before (Problems):
- High proximal values (0.80) → predicted as 0.55 ❌
- Low proximal values (0.20) → predicted as 0.45 ❌
- Identity items → 60% strongly agree ❌
- Weak distal signals override strong proximal data ❌

### After (Fixed):
- High proximal values (0.80) → predicted as 0.70-0.85 ✅
- Low proximal values (0.20) → predicted as 0.15-0.30 ✅
- Identity items → high neutral, low strongly agree ✅
- Proximal data always dominates (dampens conflicts instead of reversing) ✅

## Understanding the Output

### In your CSV, look for:

**Rationale column** will now mention:
- "Proximal topline of 0.75" (if exact match found)
- "Item type: behavior_low_friction" (auto-detected)
- "Dampened due to conflict between proximal and distal signals" (if applicable)

### Example Good Rationale:
```
Proximal topline of 0.78 indicates strong agreement (≥70% SA+A).
Qualitative themes support brand commitment. Item type: attitude
allows balanced allocation. Final: 68% agreement (within 0.70-0.85 band).
```

## Debugging Tips

### If predictions still seem off:

1. **Check if proximal topline was found:**
   - Look for `[PROXIMAL]` markers in logs
   - Check `context_summary.txt` for "Proximal topline"
   - If missing: Your quant data might not have exact concept matches

2. **Check concept type inference:**
   - Look in logs or rationale for "Item type: X"
   - If wrong: You can manually override (see Advanced Usage)

3. **Check for conflicts:**
   - Rationale should mention "dampened" if proximal vs distal conflict
   - Conflicts should move 5-10pts toward Neutral, not reverse direction

## Advanced Usage

### Manual Concept Type Override

If auto-detection is wrong, you can override in your data preparation:

```python
# In your custom runner script
from agent_estimator.ir_agent import DataParsingAgent

parser = DataParsingAgent(BASE_DIR)
bundle = parser.prepare_concept_bundle("FINANCE: Investment")

# Override the inferred type
bundle["concept_type"] = "behavior_high_friction"

# Then pass to estimator...
```

### Adding Anchor Distributions

If you have distributions from similar audiences/items:

```python
# Add to evidence bundle before estimation
bundle["anchor_sa"] = 10.0
bundle["anchor_a"] = 25.0
bundle["anchor_n"] = 35.0
bundle["anchor_sd"] = 20.0
bundle["anchor_sdd"] = 10.0

# Estimator will now consider this anchor
# Strong evidence limits anchor pull to ≤30%
```

### Manual Proximal Topline

If auto-detection misses it:

```python
# Add to evidence bundle
bundle["proximal_topline"] = 0.78

# This will trigger the hard guardrails
```

## Testing Your Setup

Run this quick test to verify everything works:

```python
from agent_estimator.ir_agent import DataParsingAgent
from pathlib import Path

# Test the IR agent
parser = DataParsingAgent(Path.cwd())
concepts = parser.list_concepts()

# Check first concept
bundle = parser.prepare_concept_bundle(concepts[0])

print(f"Concept: {concepts[0]}")
print(f"Type inferred: {bundle.get('concept_type', 'NOT FOUND')}")
print(f"Proximal topline: {bundle.get('proximal_topline', 'None')}")
print(f"Quant summary:\n{bundle.get('quant_summary', 'None')}")

# Look for [PROXIMAL] marker in quant_summary
if '[PROXIMAL]' in bundle.get('quant_summary', ''):
    print("✅ Proximal topline detected!")
else:
    print("⚠️ No proximal topline found (may be normal if no exact match)")
```

## Common Issues

### Issue: "No proximal topline found for any concept"
**Cause:** Your quantitative data questions don't exactly match concept strings

**Fix:**
- Check alignment between `concepts_to_test.csv` and column names in `Flattened Data Inputs/*.csv`
- Concepts should contain keywords from question strings
- Example: Concept "FINANCE: Savings Value" should match question "What is your savings value?"

### Issue: "All concepts inferred as 'attitude'"
**Cause:** Concept strings don't contain behavior/identity keywords

**Fix:**
- If they ARE behaviors/identity, add keywords to concept names
- Or manually override using Advanced Usage above
- Or update `_infer_concept_type()` keywords in [parser.py](agent_estimator/ir_agent/parser.py#L593)

### Issue: "Predictions still compressed toward middle"
**Cause:** Proximal toplines might not be getting through

**Fix:**
1. Generate context summary: `python generate_handpicked_context.py`
2. Check `context_summary.txt` for "[PROXIMAL]" markers
3. If missing, verify your data has exact matches
4. Try manually adding proximal_topline (see Advanced Usage)

## Files Changed

If you want to review or customize:

1. [agent_estimator/estimator_agent/prompts.py](agent_estimator/estimator_agent/prompts.py) - System prompt and prompt builder
2. [agent_estimator/ir_agent/parser.py](agent_estimator/ir_agent/parser.py) - Proximal detection and type inference
3. [agent_estimator/estimator_agent/estimator.py](agent_estimator/estimator_agent/estimator.py) - Passes new fields to prompt

## Questions?

- **Full technical details:** See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Concept type keywords:** See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md#concept-type-inference-keywords)
- **Decision workflow:** See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md#decision-workflow-as-implemented-in-system-prompt)

## Next Steps

1. ✅ Run your pipeline as normal
2. ✅ Check the rationales in output CSV
3. ✅ Compare predictions to ground truth
4. ✅ If issues persist, see Debugging Tips above
5. ✅ Consider adding anchors for even better predictions (Advanced Usage)

**The improvements are live and working automatically!**
