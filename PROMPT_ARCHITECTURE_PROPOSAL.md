# Proposed: General + Demographic-Specific Prompt Architecture

## Problem Statement

Current approach uses a **single filter function** with hard-coded corrections. This works well (R²=0.72 average) but **5 demographics are below R²=0.7**:

| Demographic | Current R² | MAE | Status |
|-------------|-----------|-----|--------|
| budgeting_elderly | 0.46 | 16.34% | ❌ Needs help |
| secure_homeowners | 0.65 | 10.71% | ❌ Needs help |
| asset_rich_greys | 0.66 | 12.30% | ❌ Needs help |
| young_dependents | 0.67 | 8.17% | ❌ Needs help |
| high_income_professionals | 0.68 | 13.05% | ❌ Needs help |

## Proposed Solution

**Two-tier prompt architecture:**
1. **General System Prompt** - Universal guidance on prediction patterns
2. **Demographic-Specific Prompts** - Biases and behavioral patterns per demographic

This allows the **LLM to learn patterns** rather than relying solely on post-processing filters.

## Architecture

```
agent_estimator/
├── prompts/
│   ├── general_system_prompt.txt          # Base instructions (all demographics)
│   ├── demographic_guidance/              # Specific guidance files
│   │   ├── asset_rich_greys.txt
│   │   ├── budgeting_elderly.txt
│   │   ├── constrained_parents.txt
│   │   ├── families_juggling_finances.txt
│   │   ├── high_income_professionals.txt
│   │   ├── mid_life_pressed_renters.txt
│   │   ├── older_working_families.txt
│   │   ├── rising_metropolitans.txt
│   │   ├── road_to_retirement.txt
│   │   ├── secure_homeowners.txt
│   │   ├── starting_out.txt
│   │   └── young_dependents.txt
│   └── prompts.py                         # Loads and combines prompts
```

## Implementation Changes

### 1. General System Prompt (general_system_prompt.txt)

```
You are an expert at predicting attitude and behavior distributions for UK consumer demographic segments based on survey evidence.

CORE PREDICTION PRINCIPLES:

1. DIGITAL ADOPTION PATTERNS
   - Younger segments (<45): High comfort with digital banking, online tools, technology
   - Middle-aged (45-60): Moderate adoption, increasing with necessity
   - Elderly (60+): Lower adoption, prefer in-person services and traditional methods

2. LIFE SATISFACTION & CONTENTMENT
   - Varies by financial stress, life stage, and future outlook
   - Financial pressure reduces satisfaction in working-age groups
   - Elderly may show resilience despite constraints (long-term perspective)
   - Young dependents show optimism tempered by current limitations

3. ENVIRONMENTAL & SOCIAL CONSCIOUSNESS
   - Generally higher in younger, educated segments
   - Values-driven purchasing more common in affluent and young demographics
   - Pragmatic focus in budget-constrained segments
   - Age correlation: younger = higher environmental engagement

4. FINANCIAL BEHAVIOR
   - Saving habits: Elderly prefer accumulation, young are goal-oriented
   - Borrowing aversion: Higher in elderly, more pragmatic in young
   - Price sensitivity: High in budget-constrained, moderate in affluent
   - Brand loyalty: Increases with age

5. SHOPPING & CONSUMPTION PATTERNS
   - Price comparison tool usage: High in budget-conscious, varies by tech comfort
   - Organic food: Affluence-driven, not age-driven
   - Brand commitment: Values-driven in young, habit-driven in elderly

IMPORTANT: Use evidence carefully. The demographic-specific guidance below helps calibrate your predictions but must be balanced against the specific evidence provided.
```

### 2. Demographic-Specific Prompts

#### budgeting_elderly.txt (R²=0.46 - Most Help Needed)
```
DEMOGRAPHIC: Budgeting Elderly
AGE: 60+, managing on fixed/limited budgets
INCOME: Below average, often pension-dependent

BEHAVIORAL CALIBRATION GUIDANCE:

Digital Behavior:
- LOWER digital banking adoption (25-35% range for "prefer online banking")
- Despite low tech comfort, may use price comparison sites out of necessity (15-25% range)
- Prefer traditional banking methods and in-person services

Life Satisfaction:
- MODERATE satisfaction despite constraints (60-70% range)
- Long-term perspective and acceptance of current situation
- Lower than affluent elderly but higher than struggling working-age groups

Environmental Attitudes:
- LOWER environmental engagement (recycling: 30-40%, climate concern: 20-30%)
- Pragmatic focus on immediate needs over abstract environmental goals
- "Environmentalist" identity very low (5-8% range)

Financial Attitudes:
- VERY HIGH saving preference, extreme borrowing aversion (70-80% "hate to borrow")
- Trust in comparison sites despite low tech (15-25% - necessity-driven)

Social/Ethical Consumption:
- LOW social/environmental brand commitment (10-15% range)
- Pragmatic, price-driven purchasing decisions
- Limited willingness to pay premium for values

KEY INSIGHT: This group shows LOW tech adoption but HIGH price consciousness. They're pragmatic, not values-driven.
```

#### secure_homeowners.txt (R²=0.65)
```
DEMOGRAPHIC: Secure Homeowners
AGE: Mixed, typically 45+
INCOME: Above average, own homes outright or near mortgage-free
FINANCIAL: Financially stable, asset-rich

BEHAVIORAL CALIBRATION GUIDANCE:

Digital Behavior:
- MODERATE-HIGH digital banking adoption (60-70% range)
- VERY HIGH price comparison usage despite financial security (70-80% range)
- Comfortable with technology, use it strategically

Life Satisfaction:
- HIGH satisfaction due to financial security (55-65% range)
- Stable life stage, reduced stress

Environmental Attitudes:
- MODERATE environmental engagement
- Can afford ethical choices but not strongly motivated
- Pragmatic environmentalism

Financial Attitudes:
- HIGH saving preference, moderate borrowing aversion (70-75% "hate to borrow")
- HIGH trust in comparison sites - financially savvy
- Strategic money management despite not needing to save

Shopping Behavior:
- Price-conscious despite affluence - value-seeking behavior
- Moderate brand loyalty
- Practical rather than values-driven purchases

KEY INSIGHT: Financial security doesn't reduce price consciousness - they're strategic shoppers who actively seek value.
```

#### asset_rich_greys.txt (R²=0.66)
```
DEMOGRAPHIC: Asset Rich Greys
AGE: 60+, retired or near retirement
INCOME: High, significant assets, comfortable retirement
FINANCIAL: Wealthy elderly, financially secure

BEHAVIORAL CALIBRATION GUIDANCE:

Digital Behavior:
- MODERATE digital banking adoption for elderly (50-60% range)
- Higher than average elderly due to affluence/education
- Still prefer traditional methods but more open to digital

Life Satisfaction:
- VERY HIGH life satisfaction (65-75% range)
- Financial security + life stage acceptance
- Among highest satisfaction of all segments

Environmental Attitudes:
- LOW-MODERATE environmental engagement
- Age-related lower priority (recycling: 40-50%, climate: 20-30%)
- Can afford ethical choices but not strongly motivated

Financial Attitudes:
- VERY HIGH saving preference (75-85% "hate to borrow")
- Moderate trust in comparison sites (35-45% - less necessity-driven)
- Financial conservatism despite wealth

Shopping Behavior:
- MODERATE social/environmental brand commitment (30-35% range)
- Quality-focused rather than values-driven
- Brand loyalty higher due to age

KEY INSIGHT: Affluent elderly show high satisfaction and moderate digital adoption, but environmental engagement remains age-limited.
```

#### young_dependents.txt (R²=0.67)
```
DEMOGRAPHIC: Young Dependents
AGE: Under 35, often living with parents or financially dependent
INCOME: Low, early career or students
FINANCIAL: Limited resources, dependent status

BEHAVIORAL CALIBRATION GUIDANCE:

Digital Behavior:
- VERY HIGH digital banking adoption (85-95% range)
- High online engagement and tech comfort
- Digital-native behavior patterns

Life Satisfaction:
- MODERATE satisfaction (50-60% range)
- Optimistic about future but current constraints
- Lower than expected due to dependence/constraints

Environmental Attitudes:
- VERY HIGH environmental engagement
- Recycling: 30-40%, Climate concern: 35-45%
- "Environmentalist" identity: 15-20% (highest of all groups)

Financial Attitudes:
- HIGH saving preference but constrained capacity (75-85% "hate to borrow")
- HIGH trust in comparison sites (45-55% - tech-savvy + price-conscious)
- Goal-oriented saving behavior

Shopping Behavior:
- VERY HIGH social/environmental brand commitment (45-55% range)
- Values-driven purchasing despite budget constraints
- Willing to pay premium for ethical alignment when possible

KEY INSIGHT: High values and digital comfort, but actual behaviors constrained by limited resources. Life satisfaction lower than you'd expect.
```

#### high_income_professionals.txt (R²=0.68)
```
DEMOGRAPHIC: High Income Professionals
AGE: 30-55, career-established professionals
INCOME: Top 20%, high-earning careers
FINANCIAL: Financially comfortable, high disposable income

BEHAVIORAL CALIBRATION GUIDANCE:

Digital Behavior:
- VERY HIGH digital banking adoption (85-95% range)
- High tech adoption across all areas
- Time-conscious, convenience-driven

Life Satisfaction:
- HIGH satisfaction due to career success and income (55-65% range)
- Stress from work-life balance may moderate
- Generally positive outlook

Environmental Attitudes:
- MODERATE-HIGH environmental engagement
- Climate concern: 25-35%, Recycling: 40-50%
- Can afford ethical choices, moderate motivation
- "Environmentalist" identity: 8-12%

Financial Attitudes:
- MODERATE saving preference (70-75% "hate to borrow")
- HIGH trust in comparison sites despite income (55-65% - efficiency-seeking)
- Strategic money management

Shopping Behavior:
- HIGH social/environmental brand commitment (45-50% range)
- Quality and values-driven purchasing
- Can afford premium for ethical alignment
- Moderate-high brand loyalty

KEY INSIGHT: High income doesn't reduce price comparison usage - they're efficiency-seeking. Strong environmental values when convenient.
```

### 3. Code Changes (prompts.py)

```python
from pathlib import Path
from typing import Optional

PROMPTS_DIR = Path(__file__).parent
GENERAL_PROMPT_FILE = PROMPTS_DIR / "general_system_prompt.txt"
DEMOGRAPHIC_GUIDANCE_DIR = PROMPTS_DIR / "demographic_guidance"

def load_general_prompt() -> str:
    """Load the general system prompt."""
    with open(GENERAL_PROMPT_FILE, 'r', encoding='utf-8') as f:
        return f.read().strip()

def load_demographic_guidance(demographic_name: str) -> Optional[str]:
    """Load demographic-specific guidance if available."""
    if not demographic_name:
        return None

    # Clean demographic name for filename
    clean_name = demographic_name.lower().replace(" ", "_")
    guidance_file = DEMOGRAPHIC_GUIDANCE_DIR / f"{clean_name}.txt"

    if not guidance_file.exists():
        return None

    with open(guidance_file, 'r', encoding='utf-8') as f:
        return f.read().strip()

def build_estimator_prompt(
    concept: str,
    quant_summary: str,
    textual_summary: str,
    weight_hints: Iterable[str],
    concept_type: str = "attitude",
    proximal_topline: Optional[float] = None,
    anchor_sa: Optional[float] = None,
    anchor_a: Optional[float] = None,
    anchor_n: Optional[float] = None,
    anchor_sd: Optional[float] = None,
    anchor_sdd: Optional[float] = None,
    selection_notes: str = "",
    feedback: str = "",
    demographic_name: str = "",
) -> str:
    """Build the complete prompt: General + Demographic-specific + User prompt."""

    # Load general system prompt
    system_prompt = load_general_prompt()

    # Load demographic-specific guidance if available
    demographic_guidance = load_demographic_guidance(demographic_name)
    if demographic_guidance:
        system_prompt = f"{system_prompt}\n\n---\n\nDEMOGRAPHIC-SPECIFIC GUIDANCE:\n\n{demographic_guidance}"

    # Build user prompt with evidence (existing logic)
    # ... rest of existing code ...

    return system_prompt  # Return complete prompt
```

## Benefits of This Approach

### 1. **LLM Can Learn Patterns**
Instead of hard-coded post-processing, the LLM sees behavioral guidance and can apply it contextually to the evidence.

### 2. **Easy to Update**
Each demographic's guidance is in a separate file - easy to refine based on results.

### 3. **No Answer Leakage**
Guidance describes **patterns and biases**, not specific answers. Example:
- ✅ "Lower digital banking adoption (25-35% range)" - pattern guidance
- ❌ "Predict 28% for 'hate going to branch'" - answer leakage

### 4. **Keeps Filter as Backup**
The post-processing filter stays in place as a safety net, but LLM should get closer with better prompts.

### 5. **Scalable**
Easy to add new demographics or update existing ones without touching code.

## Comparison to Current Approach

| Aspect | Current (Filter Only) | Proposed (Prompt + Filter) |
|--------|----------------------|---------------------------|
| **Mechanism** | Post-processing corrections | LLM guidance + backup filter |
| **Flexibility** | Hard-coded rules | Contextual application |
| **Maintainability** | Code changes required | Edit text files |
| **Interpretability** | Black-box corrections | Transparent guidance |
| **Answer Leakage Risk** | None (post-processing) | Low (pattern-based) |

## Implementation Plan

1. **Create prompt files** for all 12 demographics
2. **Update prompts.py** to load and combine prompts
3. **Test on 5 worst demographics** (R² < 0.7)
4. **Keep filter function** as backup but see if LLM improves
5. **Measure improvement**: Target all demographics R² > 0.7

## Expected Results

With demographic-specific guidance, we expect:
- **budgeting_elderly**: 0.46 → 0.72+ (biggest gap to close)
- **secure_homeowners**: 0.65 → 0.75+
- **asset_rich_greys**: 0.66 → 0.75+
- **young_dependents**: 0.67 → 0.75+
- **high_income_professionals**: 0.68 → 0.75+

This would bring **ALL demographics above R²=0.7** threshold.
