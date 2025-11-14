# Iteration 2 Analysis

## Iteration 1 Results: R² = 0.30, MAE = 13.80pp

### FIXED (Now within 3pp):
- ✅ Cut down energy: 75% vs 72.3% (2.7pp)
- ✅ Fuel consumption: 15% vs 13.4% (1.6pp)
- ✅ Good at managing money: 65% vs 62.6% (2.4pp)
- ✅ Don't like debt: 45% vs 42.3% (2.7pp)
- ✅ Switching utilities: 25% vs 27.5% (2.5pp)

**These 5 questions are now EXCELLENT!** The reasoning about friction, cost irrelevance, and competence worked.

### NEW FAILURES (Over-predicting):
- ❌ Environmental sustainability: Pred 65%, Actual 30.2% (ERROR: +35pp)
- ❌ Well insured: Pred 35%, Actual 8.5% (ERROR: +27pp)
- ❌ Healthy eating: Pred 70%, Actual 46.2% (ERROR: +24pp)
- ❌ Retirement: Pred 75%, Actual 56.4% (ERROR: +19pp)
- ❌ Cash: Pred 45%, Actual 27.6% (ERROR: +17pp)

## What Went Wrong

### Pattern: I'm OVER-PREDICTING attitudes and aspirational statements

My logic was:
- Wealthy → care about status → high environmental/health attitudes
- Wealthy → responsibility culture → high retirement responsibility
- Wealthy → self-insurance → low insurance importance (this one was still too high)

### Problem 1: Environmental Sustainability (35pp over)

**My reasoning:**
- Affluent care about status/image
- Predicted: 65% (high for image reasons)

**Why this failed:**
- I confused "environmental ACTIONS" with "think brands SHOULD do X"
- This is about BRANDS, not personal behavior
- Wealthy people are CYNICAL about corporate environmentalism
- They know it's performative
- Also: Only 8% identify as environmentalists (key signal!)

**Better reasoning:**
- Low environmentalist identity (8%) → not ideologically driven
- Question about what BRANDS should do → moderate interest
- Not about personal status/image
- Should predict: 25-35%

### Problem 2: Well Insured (27pp over)

**My reasoning:**
- Self-insurance principle
- Predicted: 35%

**Why this failed:**
- Still too high!
- Actual is 8.5% - VERY low
- Wealthy really DON'T think being "insured for everything" is important
- They insure big risks (house, life) but not "everything"

**Better reasoning:**
- Self-insurance + opportunity cost of over-insuring
- "For everything" is the key phrase - wealthy are selective
- Should predict: 5-15%

### Problem 3: Healthy Eating (24pp over)

**My reasoning:**
- Wealthy + wellness culture
- Predicted: 70%

**Why this failed:**
- Evidence: 51% eat meat, 49% vegetarian/pescatarian mix
- Mixed eating habits ≠ "healthy eating" focus
- Also: Aspiration-action gap still applies
- Wealthy might eat well, but do they PRIORITIZE healthy eating?

**Better reasoning:**
- Mixed diet signals (not all plant-based) → moderate health focus
- Aspiration exists but not extreme
- Should predict: 40-50%

### Problem 4: Retirement Responsibility (19pp over)

**My reasoning:**
- Affluent + professionals → strong self-reliance
- Predicted: 75%

**Why this failed:**
- UK has strong state pension culture
- Even wealthy believe in mixed responsibility (personal + state)
- 75% is too extreme
- Evidence: 15% plan to use investments - not that high!

**Better reasoning:**
- Self-reliance exists but not extreme
- UK culture: Balanced view of responsibility
- Should predict: 55-60%

### Problem 5: Cash Preference (17pp over)

**My reasoning:**
- Wealthy use cards
- But some still use cash
- Predicted: 45%

**Why this failed:**
- Wealthy strongly prefer digital/cards
- Evidence probably shows low cash use
- 27.6% actual means strong card preference

**Better reasoning:**
- Digital preference strong for affluent
- Cash is inefficient/outdated
- Should predict: 25-35%

## ROOT CAUSES

### Over-Correction
- I fixed the under-predictions (energy, fuel, money management)
- But over-corrected on attitudes/aspirations
- Went too high on status/image reasoning

### Missed Key Signals
- "8% environmentalists" → should have weighted this MORE heavily
- "51% eat meat" → signals NOT strong health focus
- "15% using investments for retirement" → NOT extreme self-reliance

### Status vs Cynicism
- Wealthy care about status on VISIBLE things (cars, homes)
- NOT on opinions about what brands should do
- They're cynical about corporate virtue signaling

## INSIGHTS FOR ITERATION 2

### Insight 1: Attitudes ≠ Actions
- My reasoning worked for ACTIONS (energy, fuel, money management)
- Failed for ATTITUDES (what brands should do, what's important)
- Wealthy are pragmatic, not ideological

### Insight 2: Evidence Signals Must Be Weighted
- "8% environmentalists" is a STRONG signal
- Should have predicted LOW on environmental attitude
- Can't just ignore low baseline signals

### Insight 3: "For Everything" / Extreme Language
- "Insured for EVERYTHING" → wealthy reject extremes
- "Most important feature" → wealthy reject single priorities
- They're sophisticated, balanced thinkers

### Insight 4: Cynicism About Corporate Behavior
- "Brands should consider environment" → wealthy are cynical
- They know it's marketing/greenwashing
- Don't expect high agreement

### Insight 5: Aspirations Are Moderate
- Even wealthy don't have EXTREME aspirations
- Health: Important but not obsessive (40-50%)
- Responsibility: Balanced view (55-60%), not extreme (75%)

## ITERATION 2 STRATEGY

### Fix 1: Lower Attitude Predictions
- Attitudes should be MORE MODERATE than actions
- Wealthy are pragmatic, not ideological
- Default to 30-45% for attitudes unless strong evidence

### Fix 2: Weight Low Baseline Signals More
- If evidence shows LOW % (like 8% environmentalists)
- Don't ignore it - it's telling you something important
- Predict in the lower range

### Fix 3: Interpret "For Everything" / Extremes
- Any extreme language → predict LOWER
- Wealthy reject black-and-white thinking
- "For everything" → 10-20%
- "Most important" → 10-25%
- Balanced thinking prevails

### Fix 4: Corporate Skepticism
- Questions about what OTHERS (brands, government) should do
- Wealthy are CYNICAL
- Predict MODERATE (25-40%), not high

### Fix 5: Evidence Integration
- If evidence shows 51% eat meat → NOT strong health focus
- If evidence shows 15% using investments → NOT extreme self-reliance
- If evidence shows 8% environmentalists → LOW environmental ideology
- USE these signals, don't override them with demographic assumptions

## SPECIFIC FIXES NEEDED

1. **Environmental sustainability brands**:
   - From 65% → 30%
   - Reason: Corporate cynicism + low environmentalist baseline

2. **Well insured for everything**:
   - From 35% → 10%
   - Reason: Self-insurance + "for everything" is extreme

3. **Healthy eating**:
   - From 70% → 45%
   - Reason: Mixed diet evidence + aspiration-action gap

4. **Retirement responsibility**:
   - From 75% → 58%
   - Reason: UK balanced view + moderate investment planning evidence

5. **Cash preference**:
   - From 45% → 30%
   - Reason: Digital preference strong for wealthy + cards = status

These adjustments should get us closer to R² > 0.7.
