# Failure Analysis - Exclusive Addresses (R²=-0.34)

## Current Results

| Question | Predicted | Actual | Error | Reasoning Failure |
|----------|-----------|--------|-------|-------------------|
| Environmental sustainability | 40% | 30.2% | +9.8pp | Over-predicted |
| **Cut down gas/electricity** | **30%** | **72.3%** | **-42.3pp** | **Massive under-prediction** |
| **Fuel consumption** | **45%** | **13.4%** | **+31.6pp** | **Massive over-prediction** |
| **Don't like debt** | **65%** | **42.3%** | **+22.7pp** | **Over-predicted** |
| **Good at managing money** | **35%** | **62.6%** | **-27.6pp** | **Massive under-prediction** |
| **Well insured** | **35%** | **8.5%** | **+26.5pp** | **Massive over-prediction** |
| Healthy eating | 45% | 46.2% | -1.2pp | ✅ Good! |
| **Retirement responsibility** | **40%** | **56.4%** | **-16.4pp** | **Under-predicted** |
| Switching utilities | 25% | 27.5% | -2.5pp | ✅ Good! |
| Like cash | 40% | 27.6% | +12.4pp | Over-predicted |

## Patterns in Failures

### Failures are NOT random:
- 6 massive failures (>15pp error)
- 2 good predictions (<5pp error)
- 2 moderate failures (10-15pp error)

### My reasoning was SYSTEMATICALLY WRONG about:
1. **Financial behaviors for wealthy people**
2. **What constitutes "friction" for this demographic**
3. **Confidence levels of affluent people**

## Deep Dive: Why Each Failed

### 1. "Cut down gas/electricity" - ERROR: -42pp

**My reasoning:**
- Classified as: "Behavior - High Friction"
- Logic: "Make an effort" = requires sacrifice → 25% baseline
- Predicted: 30% (slightly adjusted up)

**Why this failed:**
- Evidence showed: `Outgoings | Electricity/gas: £223` (high)
- For wealthy people, "cutting down" is NOT high friction because:
  * They have technology (smart thermostats, efficient appliances)
  * They have agency (can invest in efficiency)
  * It's about optimization, not sacrifice
- Also: Social desirability - wealthy people want to appear responsible

**What I should have reasoned:**
- High energy costs + ability to act + social desirability → HIGH adoption
- Even if it says "make an effort", for wealthy it's low friction
- Should predict: 65-75%

---

### 2. "Fuel consumption important when buying car" - ERROR: +32pp

**My reasoning:**
- Classified as: "Behavior - Low Friction" (consideration when buying)
- Evidence: `Important when buying: environmentally friendly 49%`
- Logic: 49% care about eco-friendly → predict 45%

**Why this failed:**
- I confused "environmentally friendly" (positive brand/image) with "fuel consumption" (practical/cost)
- For wealthy people buying cars:
  * They prioritize performance, brand, features
  * Fuel costs are negligible to them
  * "Eco-friendly" ≠ caring about fuel economy
- Evidence showed 49% care about "green cars" but that's about STATUS, not fuel costs

**What I should have reasoned:**
- High income + luxury car market → fuel consumption NOT important
- "Environmentally friendly" = Tesla/prestige, NOT fuel costs
- Should predict: 10-20%

---

### 3. "Don't like being in debt" - ERROR: +23pp

**My reasoning:**
- Classified as: "Attitude - Debt"
- Logic: Affluent + elderly skewing → high debt aversion 65%

**Why this failed:**
- Wealthy people use debt STRATEGICALLY (mortgages, investments, leverage)
- They're not ideologically opposed to debt
- Debt aversion is more about "can't afford it" mindset
- Wealthy people: "Debt is a tool"

**What I should have reasoned:**
- High income → comfortable with leverage → moderate debt aversion
- Should predict: 35-45%

---

### 4. "Good at managing money" - ERROR: -28pp

**My reasoning:**
- Classified as: "Identity/Competence"
- Logic: Affluent +10pp → 35% (from 25% baseline??)
- Why so low??? This makes no sense

**Why this failed:**
- I somehow used a very low baseline
- Wealthy people ARE good at managing money (how they got wealthy)
- Or they have financial advisors (still managing it well)
- High confidence + actual competence

**What I should have reasoned:**
- Affluent + directors/managers → high financial competence
- Modest self-assessment but still high → 60-65%
- Should predict: 55-65%

---

### 5. "Well insured" - ERROR: +27pp

**My reasoning:**
- Classified as: "Attitude - Insurance"
- Logic: "Sensible" + affluent → 35%

**Why this failed:**
- Wealthy people DON'T worry about insurance as much because:
  * They can self-insure (have reserves)
  * Don't need to insure everything
  * Opportunity cost of over-insuring
- "Insurance important" is more for people who CAN'T afford a loss

**What I should have reasoned:**
- Wealthy + can self-insure → LOW importance of "being insured for everything"
- Should predict: 5-15%

---

### 6. "Retirement responsibility" - ERROR: -16pp

**My reasoning:**
- Logic: Mixed signals → 40%

**Why this failed:**
- Wealthy people + professionals → STRONG belief in personal responsibility
- Evidence: `Plans to use investments for retirement: 15%`
- They're actively planning → high responsibility mindset

**What I should have reasoned:**
- Affluent + professional class → self-reliance culture strong
- Should predict: 55-60%

---

## ROOT CAUSES OF FAILURES

### 1. **Wrong Friction Classification**
- Assumed "make an effort" = high friction for everyone
- WRONG: For wealthy, many "efforts" are low friction (resources, technology, help)

### 2. **Misunderstanding Wealth Psychology**
- Insurance: Assumed sensible → important. WRONG: Wealth = can self-insure
- Debt: Assumed affluent avoid debt. WRONG: Wealth = use debt as tool
- Fuel consumption: Confused eco-status with cost-consciousness

### 3. **Evidence Misinterpretation**
- Saw "49% care about eco-friendly cars"
- Thought: They care about fuel consumption
- WRONG: Eco = status symbol (Tesla), NOT fuel economy concern

### 4. **Wrong Baselines**
- "Good at managing money": Used 25% baseline???
- Should be 50-60% for wealthy demographic

## KEY INSIGHTS FOR IMPROVED REASONING

### Principle 1: Friction is Demographic-Dependent
- What's high friction for poor is low friction for wealthy
- Wealthy have resources (money, time, help) to reduce friction
- Should reason: "Does this demographic have resources to make this easy?"

### Principle 2: Wealth Changes Motivations
- Poor: Insurance important (can't afford loss)
- Wealthy: Insurance less important (can self-insure)

- Poor: Fuel consumption matters (costs add up)
- Wealthy: Fuel consumption irrelevant (negligible cost)

- Poor: Debt aversion (can't manage it)
- Wealthy: Debt acceptance (leverage tool)

### Principle 3: Status vs Practicality
- Wealthy care about STATUS signals (eco car = Tesla)
- NOT about practical costs (fuel economy doesn't matter)

### Principle 4: Self-Insurance Principle
- Wealthy don't need insurance "for everything" - they have reserves
- This explains low insurance importance

### Principle 5: Competence Confidence
- Wealthy got there somehow (skills or inheritance with advisors)
- Either way, they're managing money well
- Should have HIGH confidence in financial management

## IMPROVED REASONING FRAMEWORK NEEDED

### Step 1: Demographic Resource Analysis
```
IF high_income AND question_involves_effort:
    CAN they reduce friction with resources?
    - Money can buy: technology, services, convenience
    - Time can enable: research, optimization
    → Reclassify friction level DOWN for wealthy
```

### Step 2: Motivation Analysis
```
WHY would this demographic care about this?
- Wealthy + fuel consumption: NO (cost irrelevant)
- Wealthy + eco cars: YES (status)
- Wealthy + insurance: NO (can self-insure)
- Wealthy + energy saving: YES (social desirability + easy)
```

### Step 3: Evidence Interpretation
```
Evidence: "49% care about eco-friendly cars"
Question: "Fuel consumption important?"

DO NOT directly transfer!
REASON: Eco cars = status/brand (Tesla, hybrid luxury)
        Fuel consumption = cost concern
        Wealthy care about first, NOT second
```

### Step 4: Confidence/Competence Calibration
```
Wealthy + financial questions:
- HIGH baseline for competence (50-60%)
- Modest adjustment (UK culture) → still 55-65%
```

## ACTION ITEMS

1. **Rewrite friction classification logic**
   - Add demographic resource consideration
   - "Make an effort" can be low friction for wealthy

2. **Add wealth-specific reasoning**
   - Self-insurance principle
   - Debt as tool vs debt as burden
   - Cost irrelevance for small expenses

3. **Improve evidence interpretation**
   - Don't directly transfer between similar concepts
   - Reason about WHY the demographic has that pattern

4. **Fix baselines for wealthy**
   - Financial competence: 50-60% baseline for affluent
   - Responsibility/self-reliance: 50-55% baseline for professionals

This will be the foundation for the improved prompt.
