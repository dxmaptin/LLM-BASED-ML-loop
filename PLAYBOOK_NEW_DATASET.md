# Playbook: Deploying the 5-Agent System to a New Dataset

## Quick Reference

This system adapts to any demographic prediction problem. Follow this systematic process to deploy on a new dataset.

---

## Step 1: Dataset Assessment (Day 1)

### What You Need
1. **Demographic profiles** (text descriptions)
2. **Survey responses** (CSV with Likert scale or similar)
3. **Ground truth** (actual answers for validation)

### Key Questions to Answer

**Q1: How many demographic groups?**
- Small (5-10): Simpler, 3-agent system might work
- Medium (10-20): Sweet spot, 5-agent system ideal
- Large (20+): 5-agent system essential

**Q2: How many questions per group?**
- Few (<20): May struggle with pattern learning
- Medium (20-100): Good for learning
- Many (100+): Excellent, can learn complex patterns

**Q3: What's the question format?**
- Likert scale (1-5): Direct fit, no adaptation needed
- Binary (yes/no): Adapt scoring, simpler distributions
- Multiple choice: May need custom output format
- Open-ended: Not suitable, needs different approach

**Q4: How similar are demographics?**
- Very similar (regional variants): May overfit, watch for it
- Diverse (income/age/lifestyle mix): Ideal, patterns emerge clearly
- Extremely diverse (cross-cultural): May need market-specific prompts

### Decision Matrix

| Demographics | Questions | Recommendation |
|--------------|-----------|----------------|
| 5-10 | <20 | ⚠️ Risky - may not have enough data |
| 5-10 | 20-100 | ✅ Good - use 3-agent system first |
| 10-20 | 20-100 | ✅ Ideal - use 5-agent system |
| 20+ | 20-100 | ✅ Perfect - use 5-agent system |
| Any | 100+ | ✅ Excellent - use 5-agent system |

---

## Step 2: Data Preparation (Days 2-3)

### Format Your Data

**Quantitative Data (CSV):**
```
Required columns:
- Demographic: Group name (e.g., "urban_millennials")
- Question: Full question text
- Response_Option: Likert scale value (e.g., "strongly_agree")
- Value: Percentage or count

Example:
urban_millennials, "I prefer sustainable products", strongly_agree, 0.35
urban_millennials, "I prefer sustainable products", slightly_agree, 0.28
...
```

**Qualitative Data (Text files):**
```
One file per demographic: [demographic_name]_profile.txt

Contents:
- Age range
- Income level
- Lifestyle characteristics
- Shopping behaviors
- Media consumption
- Values and priorities

Example:
Urban Millennials:
Age 25-35, living in cities, dual-income, no kids yet.
Digitally native, sustainability-conscious, experience over possessions.
High social media usage, influenced by peers and influencers.
```

### Create Train/Test Split

**Option A: Question-Based Split (Recommended)**
- Training: 80% of questions (Agent 1 learns from these)
- Testing: 20% of questions (held out for validation)
- All demographics included in both

**Option B: Demographic-Based Split**
- Training: 80% of demographics
- Testing: 20% of demographics (completely held out)
- All questions included

**Option C: Hybrid**
- Training: 60% questions × 80% demographics
- Testing: 40% questions × 20% demographics
- Strictest validation, but needs more data

### Validate Data Quality

Run these checks:
1. **Completeness:** Do all demographics have responses for most questions?
2. **Consistency:** Do percentages sum to 100% (or 1.0)?
3. **Coverage:** Are there enough related questions to support evidence retrieval?
4. **Balance:** Are demographics roughly similar in data availability?

**Red Flags:**
- Missing >30% of questions for any demographic
- Only 1-2 related questions per topic
- Huge imbalance (some demos have 100 questions, others have 10)

---

## Step 3: Pattern Learning (Days 4-7)

### Run Agent 1: Pattern Extractor

**Input:** All training data (demographics + questions)

**What It Does:**
1. Identifies universal patterns (apply to ALL groups)
2. Identifies demographic modifiers (how groups differ)
3. Creates general prompt (universal rules)
4. Creates class-specific prompts (demographic adjustments)

**Output:**
- `general_system_prompt.txt`
- `demographic_guidance/[demographic_name].txt` (one per demographic)

### Expected Timeline
- Small dataset (5 demos, 20 questions): 2 hours
- Medium dataset (15 demos, 50 questions): 4-6 hours
- Large dataset (25 demos, 100 questions): 8-12 hours

### What to Look For

**Good Signs:**
- Universal patterns make intuitive sense
- Demographic modifiers align with profile descriptions
- Baselines are specific (not vague like "moderate")

**Bad Signs:**
- Universal patterns contradict common sense (may be learning noise)
- All prompts look identical (not learning demographic differences)
- Baselines are extreme (90% or 5% suggests overfitting)

**If Bad:** Re-run with more explicit instructions to Agent 1 about pattern types to find.

---

## Step 4: Validation Testing (Days 8-10)

### Run Predictions on Test Set

**For Each Test Question:**
1. Agent 2: Retrieve evidence (exclude exact match in training mode)
2. Agent 3: Make prediction using general + specific prompts
3. Agent 4: Validate prediction quality
4. Aggregate: Run 5 times, average results
5. Compare: Measure error vs ground truth

**Metrics to Track:**
- R² (target: >0.70 for each demographic)
- MAE (target: <8pp average error)
- Pass rate (target: >80% of demographics)

### Iteration Strategy

**First Results Likely:**
- Overall R²: 0.55-0.65
- Some demographics work (0.75-0.85)
- Some demographics fail (0.30-0.45)

**This is NORMAL. Now iterate:**

---

## Step 5: Error Analysis & Improvement (Days 11-15)

### Identify Failure Patterns

Run Agent 5: Prompt Improver to analyze:

**Question-Level Failures:**
- Which questions consistently fail across all demographics?
- Pattern: Over-prediction or under-prediction?
- Root cause: Wrong baseline? Missing concept type?

**Demographic-Level Failures:**
- Which demographics struggle consistently?
- Pattern: All questions fail, or specific topics?
- Root cause: Poor evidence? Stereotypes in prompt?

### Common Issues & Fixes

**Issue 1: One demographic fails completely**
- **Cause:** Insufficient evidence or unique characteristics
- **Fix:** Write better class-specific prompt manually
- **Time:** 2-4 hours per demographic

**Issue 2: One question fails for all demographics**
- **Cause:** Wrong universal baseline
- **Fix:** Agent 5 updates general prompt
- **Time:** 1 day (test, validate, deploy)

**Issue 3: Stereotypes causing bias**
- **Cause:** Assumed demographic differences that don't exist
- **Fix:** Make pattern universal instead of demographic-specific
- **Example:** Our debt aversion fix (poor vs rich stereotype)
- **Time:** 2-3 days (identify, test, validate)

**Issue 4: Evidence quality problems**
- **Cause:** Not enough related questions in training data
- **Fix:** Add more training questions or relax similarity threshold
- **Time:** 1-2 days

### Iteration Loop

```
1. Run predictions on test set
2. Analyze errors (Agent 5)
3. Update prompts (general or specific)
4. Re-run predictions
5. Compare: Better? Accept. Worse? Rollback.
6. Repeat until R² > 0.70 for 80%+ demographics
```

**Expected Iterations:** 3-5 cycles
**Expected Timeline:** 1-2 weeks

---

## Step 6: Final Validation & Deployment (Days 16-20)

### Final Checks

**Accuracy Validation:**
- Overall R²: >0.75
- Pass rate: >85% of demographics
- No catastrophic failures (<0.50)

**Bias Check:**
- Are any demographic groups systematically worse?
- Do results make business sense?
- Any obvious stereotypes in prompts?

**Robustness Check:**
- Run same question 10 times, check variance
- Test edge cases (unusual questions)
- Validate confidence scoring works

### Production Deployment

**Set Up Monitoring:**
1. Track prediction confidence distribution
2. Log all low-confidence predictions for review
3. Monitor error rates by demographic
4. Alert if accuracy drops >5pp

**Document Limitations:**
1. Which questions have high error (>10pp)?
2. Which demographics are borderline (0.70-0.75 R²)?
3. What assumptions were made?
4. When should system be retrained?

**Deploy Gradually:**
- Week 1: Internal testing only
- Week 2-3: Low-stakes decisions
- Week 4+: Full production

---

## Timeline Summary

| Phase | Days | Activities | Deliverable |
|-------|------|------------|-------------|
| **Assessment** | 1 | Evaluate dataset, check feasibility | Go/No-go decision |
| **Preparation** | 2-3 | Format data, create splits, validate quality | Clean dataset |
| **Learning** | 4-7 | Run Agent 1, generate prompts | General + specific prompts |
| **Testing** | 8-10 | Run predictions, measure accuracy | Initial results (R² 0.55-0.65) |
| **Improvement** | 11-15 | Error analysis, prompt updates, iterate | Improved results (R² 0.75-0.85) |
| **Deployment** | 16-20 | Final validation, monitoring setup, docs | Production system |

**Total: 3-4 weeks from raw data to production**

---

## Adaptation Strategies by Dataset Size

### Small Dataset (5-10 demographics, <50 questions)

**Challenges:**
- Not enough data for complex pattern learning
- Risk of overfitting
- May not need 5 agents

**Adaptations:**
1. Start with 3-agent system (skip Agent 1 and 5)
2. Write prompts manually (faster than learning from small data)
3. Focus on evidence quality (Agent 2)
4. Validate heavily to catch overfitting

**Expected Accuracy:** 70-80%

### Medium Dataset (10-20 demographics, 50-150 questions)

**Sweet Spot:**
- Enough data for pattern learning
- Not too complex to manage
- 5-agent system works well

**Standard Approach:**
- Follow playbook as-is
- Expect 3-5 iterations
- Target 80-85% accuracy

### Large Dataset (20+ demographics, 150+ questions)

**Advantages:**
- Rich pattern learning
- High accuracy potential
- Robust to outliers

**Considerations:**
1. Agent 1 may take 12+ hours to run
2. More demographics = more class-specific prompts to maintain
3. May want to cluster similar demographics (e.g., "urban young" cluster)

**Expected Accuracy:** 85-90%

---

## Red Flags: When This System Won't Work

❌ **Open-ended questions** (not Likert scale or multiple choice)
- System designed for structured responses
- Would need different architecture

❌ **No demographic profiles** (only CSV responses)
- Agent 2 needs qualitative evidence
- Could work with CSV-only but accuracy drops 10-15pp

❌ **Extreme data sparsity** (<10 questions per demographic)
- Not enough to learn patterns
- Better to just use demographic profiles + human intuition

❌ **Cross-cultural prediction** (e.g., predict China from US data)
- Cultural differences too large
- Would need market-specific training

❌ **Time-sensitive questions** (e.g., "Will you vote for X tomorrow?")
- Patterns change too fast
- System assumes stable consumer preferences

---

## Success Criteria Checklist

Before deploying to production, verify:

✅ **Accuracy**
- [ ] Overall R² > 0.75
- [ ] 85%+ demographics pass (R² > 0.70)
- [ ] Average error < 8pp
- [ ] No demographic worse than R² 0.50

✅ **Quality**
- [ ] Predictions cite real evidence (not hallucinated)
- [ ] Confidence scoring works (low confidence = higher error)
- [ ] Results make business sense
- [ ] No obvious biases or stereotypes

✅ **Robustness**
- [ ] Variance across 10 runs < 3pp
- [ ] Edge cases handled gracefully
- [ ] System doesn't break on unusual questions

✅ **Operational**
- [ ] Monitoring dashboard set up
- [ ] Error logging configured
- [ ] Documentation complete
- [ ] Stakeholder training done

---

## Quick Start: 3-Day Pilot

Don't have 3 weeks? Run a quick pilot to validate feasibility:

**Day 1: Setup**
- Pick 3 representative demographics
- Pick 10 test questions
- Format data, run Agent 1

**Day 2: Test**
- Run predictions on 10 questions × 3 demographics = 30 predictions
- Calculate R² for each demographic

**Day 3: Evaluate**
- If R² > 0.60 for 2/3 demographics: **Proceed with full deployment**
- If R² 0.40-0.60 for most: **Needs work but feasible**
- If R² < 0.40 for most: **Dataset may not be suitable**

---

## Final Advice

### Do's
✅ Start with data quality (garbage in = garbage out)
✅ Validate continuously (don't wait until the end)
✅ Document assumptions (you'll forget in 2 weeks)
✅ Watch for stereotypes (data beats assumptions)
✅ Deploy gradually (pilot → low-stakes → full production)

### Don'ts
❌ Skip train/test split (you'll overfit without realizing)
❌ Overfit to test set (if iterating >10 times, something's wrong)
❌ Ignore low-confidence predictions (they're telling you something)
❌ Deploy without monitoring (accuracy will drift over time)
❌ Chase 95% accuracy (diminishing returns kick in around 85%)

---

## Key Lessons from ACORN Project

1. **Stereotypes are often wrong** - Validate assumptions with data
2. **Universal patterns > demographic differences** - Don't assume behavior varies more than it does
3. **Evidence quality matters most** - Better retrieval beats better prompts
4. **3 days of fixes can save 3 weeks** - Focus on high-impact, low-effort improvements
5. **87% is good enough** - Don't over-engineer for marginal gains

---

**Bottom Line:**
With clean data and this playbook, expect **3-4 weeks** to deploy a production-ready system with **75-85% accuracy**.

The system adapts to any demographic prediction problem - just follow the steps, watch for red flags, and iterate systematically.
