# Quick Reference: Available Prediction Metrics

## All 11 Metrics in Your Dataset

### Priority Classification

```
┌─────────────────────────────────────────────────────────────┐
│                    PRIMARY METRIC (P1)                      │
│                                                             │
│  target_top2box_intent    Purchase Intent                  │
│  Range: 0-100             The key outcome metric           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              CORE DIAGNOSTIC METRICS (P2)                   │
│              Predict these for product optimization         │
│                                                             │
│  appeal_pcttop_2          Overall emotional appeal         │
│  uniqueness_pcttop_2      Differentiation vs competitors   │
│  relevance_pcttop_2       Personal relevance/need fit      │
│  excitement_pcttop_2      Engagement level                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            EXECUTION QUALITY METRICS (P3)                   │
│            Predict for concept refinement                   │
│                                                             │
│  price_value_pcttop_2     Value for money perception       │
│  believability_pcttop     Claim credibility                │
│  understanding_pcttop_3   Concept clarity                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            BEHAVIORAL/SUMMARY METRICS (P4)                  │
│            Can be derived or predicted separately           │
│                                                             │
│  trial                    Trial intent                      │
│  inc_trial_brand          Incremental trial (new to brand) │
│  star_rating              Overall rating                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Metric Specifications

| # | Metric Name | Full Name | Range | Scale Type | Target Audience |
|---|-------------|-----------|-------|------------|-----------------|
| 1 | `target_top2box_intent` | Purchase Intent (Target) | 0-100 | Top 2 Box % | Target segment |
| 2 | `appeal_pcttop_2` | Appeal | 0-100 | Top 2 Box % | Total market |
| 3 | `uniqueness_pcttop_2` | Uniqueness | 0-100 | Top 2 Box % | Total market |
| 4 | `relevance_pcttop_2` | Relevance | 0-100 | Top 2 Box % | Total market |
| 5 | `excitement_pcttop_2` | Excitement | 0-100 | Top 2 Box % | Total market |
| 6 | `price_value_pcttop_2` | Price/Value | 0-100 | Top 2 Box % | Total market |
| 7 | `believability_pcttop` | Believability | 0-100 | Top 1 Box % | Total market |
| 8 | `understanding_pcttop_3` | Understanding | 0-100 | Top 3 Box % | Total market |
| 9 | `trial` | Trial Intent | 0-100 | % | Total market |
| 10 | `inc_trial_brand` | Incremental Trial | 0-100 | % | Total market |
| 11 | `star_rating` | Overall Rating | 0-100 | Normalized | Total market |

---

## Metric Correlations (Based on Current Data)

### Strong Correlations (r > 0.80)
**Use for validation - predictions should move together**

- `target_top2box_intent` ↔ `trial` (r ≈ 0.92)
  - If predicting 60% intent, trial should be ~58-62%

- `target_top2box_intent` ↔ `appeal_pcttop_2` (r ≈ 0.85)
  - High appeal → high intent (but not always!)

- `excitement_pcttop_2` ↔ `star_rating` (r ≈ 0.83)
  - Exciting products get higher ratings

### Moderate Correlations (r = 0.50-0.80)
**Related but can differ significantly**

- `uniqueness_pcttop_2` ↔ `excitement_pcttop_2` (r ≈ 0.72)
  - Unique products are more exciting
  - But can have unique AND boring

- `relevance_pcttop_2` ↔ `target_top2box_intent` (r ≈ 0.68)
  - Relevant products drive intent
  - But low relevance doesn't always kill intent

- `appeal_pcttop_2` ↔ `understanding_pcttop_3` (r ≈ 0.55)
  - Clearer concepts are more appealing
  - Weak link - can love without fully understanding

### Weak/Independent (r < 0.50)
**Predict independently**

- `price_value_pcttop_2` ↔ other metrics (r ≈ 0.30-0.45)
  - Value perception is independent of appeal/excitement
  - Some love the product but think it's expensive

- `believability_pcttop` ↔ most metrics (r ≈ 0.35-0.50)
  - Depends heavily on claim type
  - Can have incredible claims that hurt believability

- `inc_trial_brand` ↔ other metrics (r ≈ 0.40)
  - Brand switching behavior is complex
  - Loyal customers may love it but not be "incremental"

---

## Prediction Strategy by Use Case

### Use Case 1: Go/No-Go Decision
**Goal:** Decide whether to launch product

**Metrics to predict:**
1. `target_top2box_intent` (PRIMARY)
   - Threshold: > 60% = Green light
   - 45-60% = Yellow (test further)
   - < 45% = Red (reconsider)

2. `trial` (validation)
   - Should align with intent ±5pp

3. `star_rating` (summary check)
   - Quick overall sentiment gauge

**Prediction approach:** Simple, focus on primary metric

---

### Use Case 2: Concept Optimization
**Goal:** Identify what to fix to improve concept

**Metrics to predict (in order):**
1. `target_top2box_intent` (outcome)
2. `appeal_pcttop_2` (is it likable?)
3. `uniqueness_pcttop_2` (does it stand out?)
4. `relevance_pcttop_2` (does it fit needs?)
5. `excitement_pcttop_2` (does it engage?)
6. `price_value_pcttop_2` (is pricing right?)
7. `believability_pcttop` (are claims credible?)
8. `understanding_pcttop_3` (is it clear?)

**Diagnosis framework:**
```
IF intent is low:
  IF appeal is low → Fix: Emotional messaging, design
  IF uniqueness is low → Fix: Differentiation, innovation
  IF relevance is low → Fix: Target audience, positioning
  IF excitement is low → Fix: Claims, benefits, novelty

IF intent is OK but trial is low:
  IF price_value is low → Fix: Pricing or value perception
  IF believability is low → Fix: Claims, proof points
  IF understanding is low → Fix: Clarity, simplicity
```

**Prediction approach:** Multi-metric with diagnostic rules

---

### Use Case 3: Portfolio Comparison
**Goal:** Compare multiple concepts to pick winners

**Metrics to predict:**
1. `target_top2box_intent` (rank by this)
2. `uniqueness_pcttop_2` (identify true innovations)
3. `relevance_pcttop_2` (identify core vs niche)
4. `price_value_pcttop_2` (identify value plays)
5. `inc_trial_brand` (identify brand growers)

**Segmentation approach:**
```
STARS (High Intent + High Uniqueness)
→ Lead innovation launches

CASH COWS (High Intent + Low Uniqueness)
→ Line extensions, reliable sellers

QUESTION MARKS (Low Intent + High Uniqueness)
→ Refine or niche positioning

DOGS (Low Intent + Low Uniqueness)
→ Kill or completely rethink
```

**Prediction approach:** Batch prediction, comparative ranking

---

### Use Case 4: Pricing Strategy
**Goal:** Optimize pricing before launch

**Metrics to predict at different price points:**

Test 3 price scenarios (e.g., $12.99, $14.99, $16.99):

| Price Point | Intent | Price/Value | Trial | Inc Trial |
|-------------|--------|-------------|-------|-----------|
| $12.99 | 68% | 75% | 62% | 48% |
| $14.99 | 58% | 65% | 52% | 42% |
| $16.99 | 45% | 48% | 38% | 35% |

**Analysis:**
- Price elasticity: -15% intent per $2 increase
- Optimal price: $14.99 (balance intent × margin)

**Prediction approach:** Multiple runs with price variations

---

## Data Distribution by Metric

### Current Dataset Statistics (24 Products)

| Metric | Min | Max | Mean | Std Dev | Median |
|--------|-----|-----|------|---------|--------|
| `target_top2box_intent` | 41% | 99% | 64% | 15% | 63% |
| `appeal_pcttop_2` | 24% | 86% | 52% | 16% | 52% |
| `uniqueness_pcttop_2` | 35% | 93% | 59% | 14% | 59% |
| `relevance_pcttop_2` | 16% | 68% | 40% | 13% | 41% |
| `excitement_pcttop_2` | 59% | 98% | 78% | 10% | 81% |
| `price_value_pcttop_2` | 39% | 85% | 64% | 13% | 67% |
| `believability_pcttop` | 20% | 72% | 40% | 13% | 38% |
| `understanding_pcttop_3` | 47% | 88% | 71% | 10% | 71% |
| `trial` | 20% | 75% | 47% | 15% | 46% |
| `inc_trial_brand` | 18% | 68% | 42% | 14% | 41% |
| `star_rating` | - | - | - | - | - |

**Key insights:**
- **Excitement** has highest mean (78%) - Soap & Glory brand strength
- **Believability** has lowest mean (40%) - Bold claims hurt credibility
- **Widest range:** Intent (41-99%) - strong differentiation between concepts
- **Narrowest range:** Understanding (47-88%) - concepts are generally clear

---

## Prediction Complexity by Metric

### Easy to Predict (R² > 0.6 expected)

✅ **trial**
- Highly correlated with intent
- Can use intent as strong prior

✅ **appeal_pcttop_2**
- Clear visual signals (colors, design)
- Strong verbatim sentiment correlation

✅ **star_rating**
- Composite of other metrics
- Can derive from predictions

### Medium Difficulty (R² = 0.4-0.6 expected)

🟡 **target_top2box_intent**
- Main target metric
- Requires multi-factor integration

🟡 **excitement_pcttop_2**
- Depends on novelty perception
- Some subjectivity

🟡 **uniqueness_pcttop_2**
- Competitive context matters
- Requires market knowledge

### Hard to Predict (R² < 0.4 expected)

🔴 **price_value_pcttop_2**
- Highly dependent on pricing shown
- Reference price effects
- Current data: priced vs unpriced concepts

🔴 **believability_pcttop**
- Claim-specific
- Depends on scientific backing
- Hard to extract from vision alone

🔴 **inc_trial_brand**
- Requires brand loyalty context
- Small sample variance

---

## Recommended Prediction Sequence

### Parallel Prediction (Most Efficient)

**Batch 1: Core Perceptual Metrics**
Run simultaneously - no dependencies:
- `appeal_pcttop_2`
- `uniqueness_pcttop_2`
- `relevance_pcttop_2`
- `excitement_pcttop_2`

**Batch 2: Execution Metrics**
Run simultaneously - no dependencies:
- `price_value_pcttop_2`
- `believability_pcttop`
- `understanding_pcttop_3`

**Batch 3: Outcome Metrics**
Run with priors from Batch 1:
- `target_top2box_intent` (use appeal + uniqueness + relevance as features)
- `trial` (use intent as prior)

**Batch 4: Derived Metrics**
Calculate from previous predictions:
- `inc_trial_brand` (estimate from trial + brand metrics)
- `star_rating` (weighted average of appeal/relevance/excitement)

### Sequential Prediction (Most Accurate)

If accuracy > efficiency:

1. `understanding_pcttop_3` (clarity gates everything)
2. `appeal_pcttop_2` (emotional foundation)
3. `uniqueness_pcttop_2` (differentiation)
4. `relevance_pcttop_2` (need fit)
5. `excitement_pcttop_2` (engagement)
6. `believability_pcttop` (credibility check)
7. `price_value_pcttop_2` (value perception)
8. `target_top2box_intent` (integrate all signals)
9. `trial` (mirror of intent)
10. `inc_trial_brand` (subset of trial)
11. `star_rating` (overall summary)

**Rationale:** Later predictions use earlier ones as context

---

## Feature Requirements by Metric

### What data you MUST have to predict each metric

| Metric | Vision Data | Verbatims | KPIs | Pricing Info |
|--------|-------------|-----------|------|--------------|
| `target_top2box_intent` | ✅ Required | ✅ Required | ✅ Required | Optional |
| `appeal_pcttop_2` | ✅ Required | ✅ Required | Optional | Not needed |
| `uniqueness_pcttop_2` | ✅ Required | Optional | ✅ Required | Not needed |
| `relevance_pcttop_2` | Optional | ✅ Required | ✅ Required | Not needed |
| `excitement_pcttop_2` | ✅ Required | ✅ Required | Optional | Not needed |
| `price_value_pcttop_2` | Optional | ✅ Required | Optional | ✅ CRITICAL |
| `believability_pcttop` | Optional | ✅ Required | Optional | Not needed |
| `understanding_pcttop_3` | ✅ Required | ✅ Required | Optional | Not needed |
| `trial` | Same as intent | Same as intent | Same as intent | Same as intent |
| `inc_trial_brand` | Optional | ✅ Required | ✅ Required | Not needed |
| `star_rating` | ✅ Required | ✅ Required | Optional | Not needed |

**Legend:**
- ✅ Required = Must have for accurate prediction
- Optional = Helpful but not critical
- Not needed = Has minimal impact

---

## Quick Start: Predict Your First Metric

### Example: Predicting `appeal_pcttop_2`

```python
# In run_witty_optimist_pipeline.py

TARGET_METRIC = "appeal_pcttop_2"

METRIC_DEFINITIONS = {
    "appeal_pcttop_2": {
        "name": "Overall Appeal",
        "description": "Percentage who rate appeal as 'very appealing' or 'somewhat appealing' (top 2 box)",
        "range": "0-100",
        "baseline": 52,
        "drivers": [
            "Visual design attractiveness",
            "Emotional messaging resonance",
            "Brand affinity",
            "Color scheme preference"
        ]
    }
}

# Update estimator prompt
prompt = f"""
Predict {TARGET_METRIC} for this product concept.

Definition: {METRIC_DEFINITIONS[TARGET_METRIC]['description']}
Typical range: {METRIC_DEFINITIONS[TARGET_METRIC]['range']}
Baseline average: {METRIC_DEFINITIONS[TARGET_METRIC]['baseline']}%

Key drivers for this metric:
{chr(10).join('- ' + d for d in METRIC_DEFINITIONS[TARGET_METRIC]['drivers'])}

Evidence from vision analysis:
{vision_data}

Evidence from verbatims:
{verbatim_data}

Generate prediction (0-100):
"""
```

---

**Last Updated:** 2025-11-18
**See Also:** BLUEPRINT_EXPERIMENT_FRAMEWORK.md for full methodology
