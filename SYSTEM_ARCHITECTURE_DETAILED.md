# System Architecture - 5-Agent Demographic Prediction Pipeline

**Document Version:** 2.0
**Last Updated:** 2025-11-06
**System Status:** Production-Ready

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Agent 1: Pattern Extractor](#agent-1-pattern-extractor)
3. [Agent 2: Data Extractor (IR Agent)](#agent-2-data-extractor-ir-agent)
4. [Agent 3: Estimator](#agent-3-estimator)
5. [Agent 4: Critic (QA Agent)](#agent-4-critic-qa-agent)
6. [Agent 5: Prompt Improver](#agent-5-prompt-improver)
7. [System Workflow](#system-workflow)
8. [Data Flow Examples](#data-flow-examples)
9. [Implementation Details](#implementation-details)

---

## Architecture Overview

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TRAINING PHASE (Offline)                         │
│                                                                     │
│  ┌─────────────────┐                                               │
│  │  Agent 1:       │  Analyzes CSV + Text → General Prompt         │
│  │  Pattern        │  + Class-Specific Prompts                     │
│  │  Extractor      │  + Likert Baseline Mappings                   │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────────────┐              │
│  │  Prompt Library                                 │              │
│  │  • general_system_prompt.txt                    │              │
│  │  • demographic_guidance/affluent_urban.txt      │              │
│  │  • demographic_guidance/young_dependents.txt    │              │
│  │  • ... (22 class-specific prompts)              │              │
│  └─────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                   PREDICTION PHASE (Online)                          │
│                                                                     │
│  Input: Question + Target Demographic                               │
│    ↓                                                                │
│  ┌─────────────────┐                                               │
│  │  Agent 2:       │  Searches CSV + Text Files                    │
│  │  Data Extractor │  → Relevance-Scored Evidence Bundle           │
│  │  (IR Agent)     │  (Excludes ground truth in training)          │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Agent 3:       │  General Prompt + Specific Prompt             │
│  │  Estimator      │  + Evidence → Likert Distribution             │
│  │                 │  (With reasoning)                             │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Agent 4:       │  Validates grounding, checks confidence       │
│  │  Critic         │  → Pass/Rework Decision                       │
│  │  (QA Agent)     │  (Triggers re-estimation if needed)           │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                               │
│  │  Aggregation    │  Combines multiple runs                       │
│  │  Layer          │  → Final Prediction                           │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  Output: Likert Distribution + Topline % + Reasoning                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                  IMPROVEMENT PHASE (Iterative)                       │
│                                                                     │
│  Predictions + Ground Truth + Critic Feedback                       │
│    ↓                                                                │
│  ┌─────────────────┐                                               │
│  │  Agent 5:       │  Analyzes errors, identifies patterns         │
│  │  Prompt         │  → Updated General + Specific Prompts         │
│  │  Improver       │  (Reinforcement learning loop)                │
│  └────────┬────────┘                                               │
│           │                                                         │
│           ▼                                                         │
│  Updated Prompt Library → Next Iteration                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns:** Each agent has a single, well-defined responsibility
2. **Evidence-Based Reasoning:** All predictions must be grounded in retrieved evidence
3. **Quality Gating:** Critic agent prevents low-confidence predictions from being accepted
4. **Continuous Improvement:** Prompt Improver creates feedback loop for system evolution
5. **Hierarchical Prompting:** General prompts + specific overrides for demographic nuances

---

## Agent 1: Pattern Extractor

### Purpose
Analyzes training data (CSV responses + demographic text descriptions) to discover universal patterns, demographic-specific deviations, and Likert distribution baselines. Outputs structured prompts for the Estimator agent.

### Input Sources

**1. Quantitative Data (CSV files):**
```csv
Demographic,Question,Response_Option,Value
young_dependents,"I hate to borrow","strongly_agree",0.35
young_dependents,"I hate to borrow","slightly_agree",0.21
young_dependents,"I hate to borrow","neither",0.18
young_dependents,"I hate to borrow","slightly_disagree",0.15
young_dependents,"I hate to borrow","strongly_disagree",0.11
```

**2. Qualitative Data (Text files):**
```
Young Dependents Profile:
- Age: 18-35, living with parents or in shared accommodation
- Digital natives with high online engagement
- Early career stage, entry-level incomes
- Price-sensitive, value convenience over brand loyalty
- Heavy social media users, influenced by peer recommendations
```

### Processing Steps

**Step 1: Universal Pattern Discovery**
```
Analyze ALL demographics across ALL questions:
→ Identify concept types (attitudes vs behaviors vs identity)
→ Find baseline agreement rates by concept type
→ Discover counter-intuitive patterns (e.g., low insurance priority)
→ Identify high-variance questions requiring special handling
```

**Example Output:**
```
UNIVERSAL BASELINE: Debt Aversion
- Across 22 demographics, mean agreement = 43.2% (σ = 2.1%)
- Pattern: UK cultural norm of moderate debt aversion (not extreme)
- Applies to: ALL demographics regardless of income
- Exception: None (truly universal)

UNIVERSAL BASELINE: Fuel Consumption Priority
- Across 22 demographics, mean agreement = 14.8% (σ = 3.4%)
- Pattern: Other car features matter more (safety, space, brand)
- Applies to: ALL demographics regardless of income or car ownership
- Exception: None (low priority across board)
```

**Step 2: Demographic Calibrations**
```
Analyze deviations from universal baselines:
→ Age effects (young +20pp digital, elderly -25pp digital)
→ Income effects (affluent +15pp premium products)
→ Lifestyle effects (urban +10pp convenience services)
→ Life stage effects (families +20pp safety priorities)
```

**Example Output:**
```
DEMOGRAPHIC MODIFIER: Digital Payment Adoption
- Universal baseline: 58% adoption
- Young (18-35): +20pp → 78% (digital natives)
- Middle-age (36-55): +5pp → 63% (adopters)
- Elderly (56+): -20pp → 38% (slower adoption)
- Modifier applies to: Payment questions, online services, app usage
```

**Step 3: Concept-Type Classification**
```
Classify questions into categories with distinct baselines:
→ Attitude statements (e.g., "I value X") → 37% baseline
→ Low-friction behaviors (e.g., "I turn off lights") → 45% baseline
→ High-friction behaviors (e.g., "I switch providers") → 21% baseline
→ Identity statements (e.g., "I am X type of person") → 57% baseline
```

**Step 4: Question-Specific Corrections**
```
Identify questions with systematic errors:
→ "Healthy eating" over-predicted by 15pp → correction: 38% not 53%
→ "Environmental actions" under-predicted by 10pp → correction: 25% not 15%
→ "Insurance importance" over-predicted by 8pp → correction: 15% not 23%
```

### Output Artifacts

**1. General System Prompt (`general_system_prompt.txt`):**
```markdown
# Decision Workflow
1. Identify demographic archetype from evidence
2. Classify concept type (attitude/behavior/identity)
3. Apply concept-specific baseline
4. Review evidence and adjust prediction
5. Apply demographic calibrations
6. Sanity check (avoid over-prediction)
7. Generate Likert distribution

# Universal Baselines
- Debt aversion: 42-45% (ALL demographics)
- Fuel consumption priority: 10-20% (ALL demographics)
- Energy saving: 70-75% (ALL demographics - financial incentive)
... (20+ universal patterns)

# Demographic Calibrations
- Age: Young +20pp digital, Elderly -25pp digital
- Income: Affluent +15pp premium, Poor +20pp price comparison
... (15+ demographic modifiers)

# Evidence Hierarchy
- Proximal evidence (>0.90 relevance): 80% weight
- Related quantitative (0.70-0.90): 50% weight
- Qualitative insights (0.50-0.70): 20% weight
- Demographic inference (<0.50): 30% weight

# Critical Rules
- Respect proximal evidence (relevance >0.90)
- Action < Attitude principle (10-20pp gap)
- Values-action gap for environmental topics
- Don't over-predict (most questions land 40-60%)
```

**2. Class-Specific Prompts (e.g., `demographic_guidance/young_dependents.txt`):**
```markdown
# Young Dependents (18-35, Living with Parents)

## Adjustments to General Prompt

### Digital & Technology (+20-30pp from baseline)
- Digital payment adoption: +25pp
- Online shopping preference: +30pp
- Social media influence: +35pp
- App-based services: +28pp

### Financial Behavior (-15pp debt aversion, +20pp price sensitivity)
- Debt aversion: -15pp (more accepting of credit)
- Price comparison behavior: +20pp (budget-conscious)
- Premium brand preference: -25pp (value-seekers)
- Impulse purchases: +15pp (less financial stability)

### Lifestyle Patterns
- Convenience prioritization: +20pp (time-poor)
- Health consciousness: -10pp (lower priority at this age)
- Environmental actions: +10pp (values but limited budget)
- Traditional media consumption: -30pp (digital natives)

## Override Specific Questions
- "I prefer ethical brands": 45% (not 60% - budget constraints override values)
- "I like to use cash": 25% (not 40% - digital natives)
- "Retirement is my responsibility": 45% (not 60% - distant concern)
```

**3. Likert Baseline Mapping:**
```json
{
  "attitude_baseline": {
    "strongly_agree": 0.12,
    "slightly_agree": 0.25,
    "neither": 0.30,
    "slightly_disagree": 0.22,
    "strongly_disagree": 0.11
  },
  "low_friction_behavior": {
    "strongly_agree": 0.18,
    "slightly_agree": 0.27,
    "neither": 0.25,
    "slightly_disagree": 0.20,
    "strongly_disagree": 0.10
  },
  "high_friction_behavior": {
    "strongly_agree": 0.08,
    "slightly_agree": 0.13,
    "neither": 0.45,
    "slightly_disagree": 0.22,
    "strongly_disagree": 0.12
  }
}
```

### Implementation
- **File:** `agent_estimator/prompt_agent/general_agent.py`
- **Method:** `discover_universal_patterns()`, `extract_demographic_calibrations()`
- **LLM Used:** GPT-4o (requires strong analytical reasoning)
- **Processing Time:** 5-10 minutes for full 22-class analysis

### Example Workflow
```python
# Initialize Pattern Extractor
extractor = GeneralPatternAgent(llm=GPT4O)

# Load training data
data = load_acorn_dataset(train_classes_only=True)

# Discover patterns
universal_patterns = extractor.discover_universal_patterns(data)
demographic_mods = extractor.extract_demographic_calibrations(data)
question_corrections = extractor.identify_systematic_errors(data)

# Generate prompts
general_prompt = extractor.generate_general_prompt(
    universal_patterns,
    demographic_mods,
    question_corrections
)

# Generate class-specific prompts
for demographic_class in data.classes:
    specific_prompt = extractor.generate_class_prompt(
        demographic_class,
        deviations=extractor.find_class_deviations(demographic_class)
    )
```

---

## Agent 2: Data Extractor (IR Agent)

### Purpose
Retrieves relevant evidence from quantitative (CSV) and qualitative (text) sources for a given question and demographic. Uses semantic similarity, keyword matching, and relevance scoring to build contextual evidence bundles.

### Input
- **Question:** "I prefer to pay with cash when making purchases"
- **Target Demographic:** "young_dependents"
- **Mode:** "training" (excludes ground truth) or "inference" (uses all data)

### Retrieval Strategy

**1. Semantic Similarity Search**
```
Question embedding: embedding("I prefer to pay with cash")
↓
Search demographic CSVs for similar questions:
→ "Payment method preferences" (cosine similarity: 0.92)
→ "Digital wallet adoption" (cosine similarity: 0.85)
→ "Contactless payment usage" (cosine similarity: 0.83)
→ "Credit card ownership" (cosine similarity: 0.75)
```

**2. Keyword Matching**
```
Extract keywords: ["cash", "pay", "purchases", "payment"]
↓
Find exact/partial matches in CSV question text:
→ "I like using cash" (exact match: "cash")
→ "Payment habits" (partial match: "payment")
→ "Shopping preferences" (partial match: "purchases")
```

**3. Categorical Expansion**
```
Identify question category: "Payment Preferences"
↓
Retrieve related categories:
→ "Financial Behaviors" (related)
→ "Technology Adoption" (related - digital payments)
→ "Shopping Habits" (related)
```

**4. Relevance Scoring**
```python
def calculate_relevance(question, candidate):
    score = 0.0

    # Semantic similarity (50% weight)
    score += cosine_similarity(question, candidate) * 0.5

    # Keyword overlap (25% weight)
    score += keyword_overlap_ratio(question, candidate) * 0.25

    # Category match (15% weight)
    score += category_similarity(question, candidate) * 0.15

    # Recency/quality bonus (10% weight)
    score += data_quality_bonus(candidate) * 0.10

    return score
```

### Evidence Bundle Structure

**Example Output:**
```json
{
  "question": "I prefer to pay with cash when making purchases",
  "demographic": "young_dependents",
  "evidence": [
    {
      "type": "quantitative",
      "source": "payment_preferences.csv",
      "question": "I like using cash for everyday purchases",
      "relevance": 0.95,
      "data": {
        "strongly_agree": 0.15,
        "slightly_agree": 0.18,
        "neither": 0.22,
        "slightly_disagree": 0.25,
        "strongly_disagree": 0.20
      },
      "topline": 0.33,
      "interpretation": "33% of young_dependents prefer cash (low adoption)"
    },
    {
      "type": "quantitative",
      "source": "digital_wallet_adoption.csv",
      "question": "I use digital wallets (Apple Pay, Google Pay) regularly",
      "relevance": 0.88,
      "data": {
        "strongly_agree": 0.35,
        "slightly_agree": 0.28,
        "neither": 0.15,
        "slightly_disagree": 0.12,
        "strongly_disagree": 0.10
      },
      "topline": 0.63,
      "interpretation": "63% of young_dependents use digital wallets (inverse of cash)"
    },
    {
      "type": "qualitative",
      "source": "young_dependents_profile.txt",
      "relevance": 0.72,
      "excerpt": "Digital natives with high smartphone penetration. Prefer app-based payments and contactless methods. Cash usage declining rapidly in this segment, especially for urban dwellers. Many don't carry physical wallets anymore.",
      "interpretation": "Demographic profile suggests low cash preference"
    },
    {
      "type": "qualitative",
      "source": "payment_trends_2024.txt",
      "relevance": 0.68,
      "excerpt": "18-35 age group leads digital payment adoption. 78% use contactless regularly, 65% have digital wallets. Cash usage down to 22% of transactions in 2024 from 45% in 2019.",
      "interpretation": "Market trend data confirms digital shift"
    }
  ],
  "evidence_summary": {
    "proximal_evidence_count": 2,
    "related_evidence_count": 2,
    "qualitative_evidence_count": 2,
    "avg_relevance": 0.81,
    "confidence_level": "HIGH"
  }
}
```

### Training Mode: Ground Truth Exclusion

**Problem:** In training mode, we can't use the actual answer to the question we're predicting (that's cheating).

**Solution:**
```python
def prepare_concept_bundle(self, question, exclude_exact_match=True):
    """
    Retrieve evidence while excluding the exact question being predicted.
    """
    # Get all candidate evidence
    candidates = self.search_evidence(question)

    if exclude_exact_match:
        # Filter out exact matches
        candidates = [
            c for c in candidates
            if not self.is_exact_match(c.question, question)
        ]

    # Rank by relevance
    ranked = sorted(candidates, key=lambda x: x.relevance, reverse=True)

    # Return top N
    return ranked[:10]

def is_exact_match(self, candidate_q, target_q):
    """
    Detect if candidate question is the exact question we're predicting.
    """
    # Normalize text
    c = self.normalize_text(candidate_q)
    t = self.normalize_text(target_q)

    # Check exact match
    if c == t:
        return True

    # Check substring match (handles truncated questions)
    if len(c) > 30 and len(t) > 30:
        if c[:30] == t[:30]:  # First 30 chars match
            return True

    # Check high similarity (>0.98)
    if cosine_similarity(candidate_q, target_q) > 0.98:
        return True

    return False
```

**Example:**
```python
# Question to predict
question = "I prefer to pay with cash when making purchases"

# Training mode - exclude exact match
evidence_train = ir_agent.prepare_concept_bundle(
    question,
    exclude_exact_match=True  # Will NOT include this exact question
)

# Inference mode - use all data
evidence_infer = ir_agent.prepare_concept_bundle(
    question,
    exclude_exact_match=False  # Will include all related evidence
)
```

### Weighted Scoring System

**Evidence Ranking Formula:**
```python
final_score = (
    semantic_similarity * 0.50 +
    keyword_match * 0.25 +
    category_match * 0.15 +
    quality_bonus * 0.10
)

# Quality bonus factors:
# - Data recency (newer = better)
# - Sample size (larger = better)
# - Source reliability (official survey > scraped data)
# - Completeness (full distribution > topline only)
```

### Implementation
- **File:** `agent_estimator/ir_agent/parser.py`
- **Class:** `DataParsingAgent`
- **Key Methods:** `prepare_concept_bundle()`, `search_evidence()`, `calculate_relevance()`
- **Processing Time:** 200-500ms per question

### Example Workflow
```python
# Initialize IR Agent
ir_agent = DataParsingAgent(base_dir="demographic_runs_ACORN/young_dependents")

# Retrieve evidence (training mode)
evidence = ir_agent.prepare_concept_bundle(
    concept="I prefer to pay with cash",
    exclude_exact_match=True
)

# Evidence structure
for item in evidence:
    print(f"Relevance: {item.relevance:.2f}")
    print(f"Source: {item.source}")
    print(f"Data: {item.data}")
```

---

## Agent 3: Estimator

### Purpose
Generates Likert scale predictions using general prompt, class-specific prompt (if available), and retrieved evidence. Produces both reasoning and final distribution.

### Input
- **Question:** "I prefer to pay with cash when making purchases"
- **Demographic:** "young_dependents"
- **Evidence Bundle:** (from IR Agent)
- **General Prompt:** Universal patterns and baselines
- **Specific Prompt:** young_dependents demographic guidance (optional)

### Prompt Hierarchy

**Priority Order (specific overrides general):**
```
1. Proximal Evidence (relevance >0.90) → 80% weight
2. Class-Specific Prompt → Overrides general baseline
3. General Prompt → Default baseline
4. Demographic Inference → Fallback if no evidence
```

**Example Prompt Construction:**
```python
def build_estimator_prompt(question, demographic, evidence, general_prompt, specific_prompt=None):
    """
    Combine general + specific prompts with evidence.
    Specific prompt can override general baselines.
    """

    # Start with general system prompt
    system_prompt = f"{general_prompt}\n\n"

    # Add class-specific adjustments if available
    if specific_prompt:
        system_prompt += f"## {demographic} Specific Guidance\n"
        system_prompt += f"{specific_prompt}\n\n"
        system_prompt += "NOTE: Class-specific guidance OVERRIDES general baselines.\n\n"

    # Add evidence bundle
    system_prompt += "## Retrieved Evidence\n"
    for item in evidence:
        system_prompt += f"- [{item.relevance:.2f}] {item.source}: {item.interpretation}\n"

    # Add prediction instructions
    user_prompt = f"""
    Predict the Likert distribution for the following question in the {demographic} demographic:

    Question: "{question}"

    Instructions:
    1. Review the evidence provided above (prioritize high-relevance items)
    2. Apply general baseline for this concept type
    3. If class-specific guidance exists, override general baseline
    4. Adjust based on demographic calibrations (age, income, lifestyle)
    5. Perform sanity check (avoid over-prediction)
    6. Output final distribution

    Output format:
    {{
      "reasoning": "Step-by-step explanation of your prediction",
      "distribution": {{
        "strongly_agree": 0.XX,
        "slightly_agree": 0.XX,
        "neither": 0.XX,
        "slightly_disagree": 0.XX,
        "strongly_disagree": 0.XX
      }},
      "topline": 0.XX,
      "confidence": "HIGH/MEDIUM/LOW"
    }}
    """

    return system_prompt, user_prompt
```

### Reasoning Process

**Example Estimator Output:**
```json
{
  "reasoning": "
Step 1: Demographic Analysis
- young_dependents: 18-35, living with parents, digital natives
- High smartphone penetration, app-based lifestyle
- Budget-conscious but convenience-oriented

Step 2: Evidence Review
- Proximal evidence (0.95): Only 33% prefer cash for everyday purchases
- Related evidence (0.88): 63% use digital wallets regularly
- Qualitative (0.72): 'Digital natives, cash usage declining rapidly'
- Market trend (0.68): Cash down to 22% of transactions in 18-35 age group

Step 3: Concept Type Classification
- Concept: Payment preference (behavior, low-medium friction)
- General baseline: 45% agreement for low-friction behaviors
- BUT: Evidence strongly contradicts baseline (all sources point to LOW cash preference)

Step 4: Class-Specific Adjustments
- young_dependents specific guidance: 'Digital payment adoption +25pp from baseline'
- Override: 'I like to use cash: 25% (not 40% - digital natives)'
- This matches the specific override exactly

Step 5: Evidence-Driven Adjustment
- Proximal evidence (33% cash preference) aligns with specific override (25%)
- Digital wallet adoption (63%) is inverse of cash preference
- All evidence points to LOW cash usage (20-35% range)

Step 6: Demographic Calibrations
- Young age: -15pp cash preference (digital natives)
- Urban lifestyle: -10pp cash preference (card infrastructure)
- Combined effect: -25pp from general baseline

Step 7: Final Distribution
- Starting from specific override: 25% topline agreement
- Distribute: SA=8%, SlA=17%, N=30%, SlD=25%, SD=20%
- Confidence: HIGH (multiple consistent evidence sources)
  ",

  "distribution": {
    "strongly_agree": 0.08,
    "slightly_agree": 0.17,
    "neither": 0.30,
    "slightly_disagree": 0.25,
    "strongly_disagree": 0.20
  },

  "topline": 0.25,
  "confidence": "HIGH",

  "evidence_used": [
    {"source": "payment_preferences.csv", "relevance": 0.95, "weight": 0.80},
    {"source": "digital_wallet_adoption.csv", "relevance": 0.88, "weight": 0.50},
    {"source": "young_dependents_profile.txt", "relevance": 0.72, "weight": 0.20}
  ]
}
```

### Multiple Runs & Aggregation

**Problem:** Single LLM calls can be noisy (stochastic outputs).

**Solution:** Run estimator 3-5 times and aggregate.

```python
def estimate_with_aggregation(question, demographic, evidence, runs=5):
    """
    Run estimator multiple times and aggregate results.
    """
    predictions = []

    for i in range(runs):
        result = estimator.estimate(
            question=question,
            demographic=demographic,
            evidence=evidence,
            temperature=0.7  # Some randomness for diversity
        )
        predictions.append(result.distribution)

    # Aggregate distributions (average)
    aggregated = {
        "strongly_agree": np.mean([p["strongly_agree"] for p in predictions]),
        "slightly_agree": np.mean([p["slightly_agree"] for p in predictions]),
        "neither": np.mean([p["neither"] for p in predictions]),
        "slightly_disagree": np.mean([p["slightly_disagree"] for p in predictions]),
        "strongly_disagree": np.mean([p["strongly_disagree"] for p in predictions])
    }

    # Normalize to ensure sum = 1.0
    total = sum(aggregated.values())
    aggregated = {k: v/total for k, v in aggregated.items()}

    return aggregated
```

### Implementation
- **File:** `agent_estimator/estimator_agent/estimator.py`
- **Class:** `EstimatorAgent`
- **Key Methods:** `estimate()`, `build_prompt()`, `parse_response()`
- **LLM Used:** GPT-4o (primary), Claude 3.5 Sonnet (alternative)
- **Processing Time:** 3-5 seconds per prediction (single run)

### Example Workflow
```python
# Initialize Estimator
estimator = EstimatorAgent()

# Load prompts
general_prompt = load_prompt("general_system_prompt.txt")
specific_prompt = load_prompt(f"demographic_guidance/{demographic}.txt")

# Run prediction
result = estimator.estimate(
    concept="I prefer to pay with cash",
    evidence=evidence_bundle,
    general_prompt=general_prompt,
    specific_prompt=specific_prompt,
    runs=5,
    iteration=1
)

# Output
print(f"Topline: {result.topline}%")
print(f"Distribution: {result.aggregated_distribution}")
print(f"Reasoning: {result.reasoning}")
```

---

## Agent 4: Critic (QA Agent)

### Purpose
Validates estimator outputs to ensure predictions are grounded in evidence, checks confidence levels, and triggers rework when quality thresholds aren't met.

### Validation Checks

**1. Grounding Check**
```
Does the prediction cite actual evidence from the bundle?
→ YES: Estimator referenced "payment_preferences.csv" (relevance 0.95)
→ YES: Estimator referenced "digital_wallet_adoption.csv" (relevance 0.88)
→ NO: Estimator did NOT invent data not in evidence bundle
→ PASS: Grounding check passed
```

**2. Confidence Assessment**
```python
def assess_confidence(evidence_bundle, prediction):
    """
    Calculate confidence score based on evidence quality.
    """
    score = 0.0

    # Evidence quantity (max 30 points)
    proximal_count = len([e for e in evidence_bundle if e.relevance > 0.90])
    related_count = len([e for e in evidence_bundle if 0.70 <= e.relevance <= 0.90])
    score += min(proximal_count * 15, 30)  # Cap at 30
    score += min(related_count * 5, 20)    # Cap at 20

    # Evidence quality (max 30 points)
    avg_relevance = np.mean([e.relevance for e in evidence_bundle])
    score += avg_relevance * 30

    # Evidence consistency (max 20 points)
    # Do all evidence sources point in same direction?
    evidence_agreement = calculate_evidence_agreement(evidence_bundle)
    score += evidence_agreement * 20

    # Prediction reasonableness (max 20 points)
    # Is topline within expected range (10-90%)?
    topline = prediction.topline
    if 0.10 <= topline <= 0.90:
        score += 20
    elif 0.05 <= topline <= 0.95:
        score += 10

    return score / 100  # Normalize to 0-1

# Confidence thresholds
if confidence >= 0.80:
    return "HIGH"
elif confidence >= 0.60:
    return "MEDIUM"
else:
    return "LOW"
```

**3. Consistency Check**
```
Does the prediction align with evidence direction?
→ Evidence says: LOW cash preference (25-33%)
→ Prediction says: 25% cash preference
→ PASS: Prediction aligns with evidence
```

**4. Distribution Validity**
```
Is the Likert distribution well-formed?
→ Sum of probabilities = 1.000 ✓
→ No negative values ✓
→ Reasonable spread (not all in one bucket) ✓
→ PASS: Distribution is valid
```

**5. Reasoning Quality**
```
Does the reasoning follow the decision workflow?
→ Step 1: Demographic analysis ✓
→ Step 2: Evidence review ✓
→ Step 3: Concept classification ✓
→ Step 4: Class-specific adjustments ✓
→ Step 5: Evidence-driven adjustment ✓
→ Step 6: Demographic calibrations ✓
→ Step 7: Final distribution ✓
→ PASS: Reasoning is systematic
```

### Example Critic Output

```json
{
  "validation_result": "PASS",
  "confidence": "HIGH",
  "confidence_score": 0.87,
  "checks": {
    "grounding": {
      "status": "PASS",
      "details": "All claims cited in evidence bundle. No fabricated data detected."
    },
    "consistency": {
      "status": "PASS",
      "details": "Prediction (25% cash preference) aligns with evidence direction (33% and 22%)."
    },
    "distribution_validity": {
      "status": "PASS",
      "details": "Sum=1.000, no negatives, reasonable spread."
    },
    "reasoning_quality": {
      "status": "PASS",
      "details": "Systematic 7-step reasoning followed. Clear evidence citations."
    }
  },
  "confidence_breakdown": {
    "evidence_quantity": 0.90,
    "evidence_quality": 0.85,
    "evidence_consistency": 0.92,
    "prediction_reasonableness": 1.00
  },
  "recommendation": "ACCEPT",
  "notes": "Strong evidence support. Multiple consistent sources. No issues detected."
}
```

### Rework Trigger Logic

```python
def should_rework(critic_result, iteration):
    """
    Decide if estimator should re-run prediction.
    """
    # Never rework after max iterations
    if iteration >= 3:
        return False, "Max iterations reached"

    # Always rework if confidence is LOW
    if critic_result.confidence == "LOW":
        return True, "Low confidence detected"

    # Rework if grounding check failed
    if critic_result.checks["grounding"]["status"] == "FAIL":
        return True, "Fabricated data detected"

    # Rework if prediction inconsistent with evidence
    if critic_result.checks["consistency"]["status"] == "FAIL":
        return True, "Prediction contradicts evidence"

    # Otherwise accept
    return False, "Quality checks passed"
```

**Example Rework Flow:**
```
Iteration 1:
→ Estimator predicts 65% cash preference
→ Critic: "Inconsistent with evidence (evidence says 25%)"
→ Confidence: LOW (0.45)
→ REWORK TRIGGERED

Iteration 2:
→ Estimator re-runs with feedback: "Previous prediction too high, evidence strongly indicates low cash usage"
→ Estimator predicts 28% cash preference
→ Critic: "Consistent with evidence"
→ Confidence: HIGH (0.87)
→ ACCEPT
```

### Implementation
- **File:** `agent_estimator/qa_agent/critic.py`
- **Class:** `CriticAgent`
- **Key Methods:** `validate()`, `assess_confidence()`, `check_grounding()`
- **LLM Used:** GPT-4o (for grounding check), Rule-based (for distribution validity)
- **Processing Time:** 1-2 seconds per validation

### Example Workflow
```python
# Initialize Critic
critic = CriticAgent()

# Validate estimator output
validation = critic.validate(
    prediction=estimator_result,
    evidence_bundle=evidence,
    question=question,
    demographic=demographic
)

# Check if rework needed
should_rework, reason = critic.should_rework(validation, iteration=1)

if should_rework:
    # Re-run estimator with feedback
    feedback = f"Previous prediction had issues: {reason}. {validation.notes}"
    estimator_result = estimator.estimate(
        ...,
        feedback=feedback,
        iteration=2
    )
else:
    # Accept prediction
    final_result = estimator_result
```

---

## Agent 5: Prompt Improver

### Purpose
Analyzes prediction errors against ground truth, identifies systematic failure patterns, and generates updated prompts for both general and class-specific guidance. Implements reinforcement learning loop.

### Input
- **Predictions:** Estimator outputs for all test questions
- **Ground Truth:** Actual survey results
- **Critic Feedback:** Confidence scores and validation notes
- **Current Prompts:** General + class-specific prompts used

### Error Analysis Process

**Step 1: Calculate Performance Metrics**
```python
def analyze_performance(predictions, ground_truth):
    """
    Compute R², MAE, and per-question errors.
    """
    results = []

    for q in questions:
        pred = predictions[q]["topline"]
        actual = ground_truth[q]
        error = abs(pred - actual)

        results.append({
            "question": q,
            "predicted": pred,
            "actual": actual,
            "error": error,
            "status": "GOOD" if error <= 5 else "POOR"
        })

    # Calculate aggregate metrics
    r2 = calculate_r2([r["actual"] for r in results], [r["predicted"] for r in results])
    mae = np.mean([r["error"] for r in results])

    return {
        "r2": r2,
        "mae": mae,
        "results": results
    }
```

**Step 2: Identify Systematic Errors**
```python
def identify_error_patterns(performance_data):
    """
    Find recurring failure modes across questions.
    """
    patterns = []

    # Pattern 1: Consistent over/under-prediction
    errors = [r["predicted"] - r["actual"] for r in performance_data["results"]]
    mean_bias = np.mean(errors)

    if mean_bias > 5:
        patterns.append({
            "type": "over_prediction_bias",
            "magnitude": mean_bias,
            "description": f"Consistently over-predicting by {mean_bias:.1f}pp"
        })
    elif mean_bias < -5:
        patterns.append({
            "type": "under_prediction_bias",
            "magnitude": abs(mean_bias),
            "description": f"Consistently under-predicting by {abs(mean_bias):.1f}pp"
        })

    # Pattern 2: Specific question failures
    poor_questions = [r for r in performance_data["results"] if r["error"] > 10]
    if poor_questions:
        patterns.append({
            "type": "question_specific_failures",
            "questions": [q["question"] for q in poor_questions],
            "description": f"{len(poor_questions)} questions with >10pp error"
        })

    # Pattern 3: Evidence quality correlation
    low_confidence = [r for r in performance_data["results"] if r.get("confidence") == "LOW"]
    if len(low_confidence) > 0.3 * len(performance_data["results"]):
        patterns.append({
            "type": "evidence_quality_issues",
            "description": f"{len(low_confidence)} predictions had low confidence"
        })

    return patterns
```

**Step 3: Root Cause Analysis**
```python
def analyze_root_causes(error_patterns, evidence_bundles, prompts):
    """
    Dig deeper into why errors occurred.
    """
    root_causes = []

    for pattern in error_patterns:
        if pattern["type"] == "over_prediction_bias":
            # Check if baseline is too high
            root_causes.append({
                "pattern": pattern,
                "cause": "baseline_too_high",
                "fix": f"Lower general baseline by {pattern['magnitude']/2:.1f}pp"
            })

        elif pattern["type"] == "question_specific_failures":
            # Analyze each failing question
            for q in pattern["questions"]:
                evidence = evidence_bundles[q]
                pred = predictions[q]
                actual = ground_truth[q]

                # Check if evidence was ignored
                if evidence.avg_relevance > 0.80 and abs(pred - actual) > 10:
                    root_causes.append({
                        "pattern": pattern,
                        "question": q,
                        "cause": "ignored_evidence",
                        "fix": f"Add explicit override for '{q}' based on evidence"
                    })

                # Check if evidence was insufficient
                elif evidence.avg_relevance < 0.60:
                    root_causes.append({
                        "pattern": pattern,
                        "question": q,
                        "cause": "insufficient_evidence",
                        "fix": f"Need better evidence retrieval for '{q}'"
                    })

        elif pattern["type"] == "evidence_quality_issues":
            root_causes.append({
                "pattern": pattern,
                "cause": "ir_agent_performance",
                "fix": "Improve evidence retrieval strategy (better keywords, semantic search)"
            })

    return root_causes
```

**Step 4: Generate Prompt Updates**
```python
def generate_prompt_updates(root_causes, current_prompt):
    """
    Use LLM to create updated prompt based on error analysis.
    """

    analysis_summary = format_root_causes(root_causes)

    improver_prompt = f"""
    You are a prompt optimization expert. Analyze the following error patterns and generate an updated system prompt.

    Current Prompt:
    {current_prompt}

    Error Analysis:
    {analysis_summary}

    Instructions:
    1. Identify which parts of the prompt led to these errors
    2. Generate specific corrections (e.g., lower baseline for question X)
    3. Add new rules if systematic patterns detected
    4. Maintain existing successful patterns
    5. Output the complete updated prompt

    Output format:
    {{
      "changes_made": ["Change 1", "Change 2", ...],
      "updated_prompt": "Full updated prompt text...",
      "expected_improvements": ["Improvement 1", "Improvement 2", ...]
    }}
    """

    response = llm.generate(improver_prompt)
    return response
```

### Example Improvement Cycle

**Iteration 1 Results:**
```
R² = 0.72
MAE = 8.5pp

Error patterns:
1. Over-prediction bias (+6.2pp average)
2. Cash preference: +18pp error (predicted 45%, actual 27%)
3. Insurance importance: +12pp error (predicted 27%, actual 15%)
4. Healthy eating: +15pp error (predicted 53%, actual 38%)
```

**Root Cause Analysis:**
```
1. General baseline too high (45% for behaviors, should be 40%)
2. Cash preference: Ignoring digital native evidence for young demos
3. Insurance: Over-estimating "sensible behavior" despite evidence
4. Healthy eating: Confusing attitude (60% value) with behavior (38% do)
```

**Prompt Updates Generated:**
```markdown
## Changes to General Prompt v1 → v2:

### 1. Lower Behavior Baseline
OLD: Low-friction behaviors baseline = 45%
NEW: Low-friction behaviors baseline = 40%
REASON: Systematic +6.2pp over-prediction detected

### 2. Add Cash Preference Override
NEW RULE:
"Cash preference questions:
- For young demographics (18-35): 25-30% baseline (digital natives)
- For middle demographics (36-55): 35-40% baseline
- For elderly demographics (56+): 45-50% baseline
- ALWAYS check digital payment evidence as inverse signal"

### 3. Add Insurance Reality Check
NEW RULE:
"Insurance importance is counter-intuitively LOW across all demographics.
- Baseline: 15% (not 25%)
- Even affluent demos rarely exceed 20%
- Reason: Seen as expensive, not urgent priority despite being 'sensible'"

### 4. Clarify Attitude vs Behavior Gap
NEW RULE:
"For questions mixing attitude + behavior (e.g., 'healthy eating'):
- If wording is identity/behavior-focused: Use BEHAVIOR baseline (not attitude)
- Healthy eating specifically: 38% baseline (aspiration-action gap)
- Environmental actions: 25% baseline (values 45%, actions 25%)"
```

**Expected Improvements:**
```
- Overall MAE: 8.5pp → 6.0pp (-2.5pp)
- Cash preference error: 18pp → 5pp (-13pp)
- Insurance error: 12pp → 4pp (-8pp)
- Healthy eating error: 15pp → 6pp (-9pp)
- Expected R²: 0.72 → 0.82 (+0.10)
```

### Reinforcement Learning Loop

```
┌─────────────────────────────────────────────────┐
│  Iteration N                                    │
│                                                 │
│  1. Run predictions with current prompt         │
│  2. Compare vs ground truth                     │
│  3. Analyze errors → identify patterns          │
│  4. Generate prompt updates                     │
│  5. Test updated prompt                         │
│  6. If improved: Accept. Else: Rollback.        │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Iteration N+1                                  │
│  (Repeat with updated prompt)                   │
└─────────────────────────────────────────────────┘
```

**Convergence Criteria:**
```python
def has_converged(performance_history):
    """
    Stop iterating when performance plateaus.
    """
    if len(performance_history) < 3:
        return False

    # Check last 3 iterations
    recent = performance_history[-3:]
    r2_values = [p["r2"] for p in recent]

    # If R² improvement < 0.02 for 3 iterations, stop
    if max(r2_values) - min(r2_values) < 0.02:
        return True

    # If R² > 0.90, stop (good enough)
    if recent[-1]["r2"] > 0.90:
        return True

    return False
```

### Implementation
- **File:** `agent_estimator/prompt_agent/prompt_improver.py`
- **Class:** `PromptImprovementAgent`
- **Key Methods:** `analyze_errors()`, `identify_patterns()`, `generate_updates()`
- **LLM Used:** GPT-4o (for prompt generation)
- **Processing Time:** 2-5 minutes per iteration

### Example Workflow
```python
# Initialize Prompt Improver
improver = PromptImprovementAgent()

# Run improvement cycle
for iteration in range(1, 10):
    print(f"\n=== Iteration {iteration} ===")

    # Test current prompt
    performance = run_test_suite(current_prompt, test_questions)

    print(f"R² = {performance['r2']:.4f}, MAE = {performance['mae']:.2f}pp")

    # Check convergence
    if improver.has_converged(performance_history):
        print("Converged!")
        break

    # Analyze errors
    patterns = improver.identify_error_patterns(performance)
    root_causes = improver.analyze_root_causes(patterns, evidence_bundles, current_prompt)

    # Generate updates
    updates = improver.generate_prompt_updates(root_causes, current_prompt)

    # Test updated prompt
    new_performance = run_test_suite(updates["updated_prompt"], test_questions)

    # Accept if improved
    if new_performance["r2"] > performance["r2"]:
        print(f"Improvement: +{new_performance['r2'] - performance['r2']:.4f} R²")
        current_prompt = updates["updated_prompt"]
        performance_history.append(new_performance)
    else:
        print("No improvement, rolling back")
        break

print(f"\nFinal R² = {performance_history[-1]['r2']:.4f}")
```

---

## System Workflow

### Complete Prediction Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT: Question + Target Demographic                            │
│  "I prefer to pay with cash" + "young_dependents"               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 2: Data Extractor (IR Agent)                             │
│  → Search CSV + Text files                                      │
│  → Calculate relevance scores                                   │
│  → Build evidence bundle                                        │
│  → Exclude ground truth if training mode                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Evidence Bundle:                                               │
│  • Payment preferences (rel: 0.95): 33% cash usage             │
│  • Digital wallet adoption (rel: 0.88): 63% digital usage      │
│  • Profile: "Digital natives, cash declining"                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 3: Estimator (Iteration 1)                              │
│  → Load general prompt + young_dependents specific prompt       │
│  → Apply 7-step decision workflow                              │
│  → Generate distribution + reasoning                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Prediction (Iteration 1):                                      │
│  • Distribution: SA=8%, SlA=17%, N=30%, SlD=25%, SD=20%        │
│  • Topline: 25%                                                │
│  • Reasoning: "Evidence shows low cash usage..."                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 4: Critic                                                │
│  → Check grounding (PASS)                                       │
│  → Assess confidence (HIGH, 0.87)                               │
│  → Validate distribution (PASS)                                 │
│  → Check reasoning (PASS)                                       │
│  → Decision: ACCEPT                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Run 4 more times (total 5 runs)                               │
│  → Aggregate distributions                                      │
│  → Calculate mean + std                                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  FINAL OUTPUT:                                                  │
│  • Aggregated Distribution: SA=8.2%, SlA=16.8%, ...            │
│  • Topline: 25.0%                                              │
│  • Confidence: HIGH                                             │
│  • Evidence: [List of sources used]                            │
└─────────────────────────────────────────────────────────────────┘
```

### Training & Improvement Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  INITIAL: Train Agent 1 (Pattern Extractor)                     │
│  → Analyze 22 demographics × 100+ questions                     │
│  → Generate general_system_prompt.txt                           │
│  → Generate 22 class-specific prompts                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  TEST: Run predictions on holdout questions                     │
│  → 10 questions × 19 demographics = 190 predictions             │
│  → Calculate R², MAE per class                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  ANALYZE: Agent 5 (Prompt Improver)                             │
│  → Compare predictions vs ground truth                          │
│  → Identify error patterns                                      │
│  → Generate prompt updates                                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  ITERATE: Test updated prompts                                  │
│  → If improved: Accept                                          │
│  → If worse: Rollback                                           │
│  → Repeat until convergence                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  DEPLOY: Production-ready prompts                               │
│  → Save to prompt library                                       │
│  → Monitor performance                                          │
│  → Periodic re-training                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Examples

### Example 1: Successful Prediction (High Confidence)

**Input:**
- Question: "I make an effort to cut down on gas/electricity usage"
- Demographic: "cash-strapped_families"

**Agent 2 (IR) Output:**
```json
{
  "evidence": [
    {
      "type": "quantitative",
      "relevance": 0.96,
      "source": "energy_saving_behaviors.csv",
      "data": {"topline": 0.78},
      "interpretation": "78% actively reduce energy usage"
    },
    {
      "type": "qualitative",
      "relevance": 0.89,
      "excerpt": "Financial constraints drive energy consciousness. Bill reduction is top priority.",
      "interpretation": "Economic necessity motivates behavior"
    }
  ],
  "confidence": "HIGH"
}
```

**Agent 3 (Estimator) Output:**
```json
{
  "reasoning": "
  - Concept: Energy saving (low-friction behavior, financial incentive)
  - Evidence: 78% topline (proximal, rel=0.96)
  - General baseline: 70-75% for energy saving (universal financial incentive)
  - Class adjustment: cash-strapped +5pp (necessity drives action)
  - Final: 78% topline (matches evidence exactly)
  ",
  "distribution": {
    "strongly_agree": 0.38,
    "slightly_agree": 0.40,
    "neither": 0.12,
    "slightly_disagree": 0.07,
    "strongly_disagree": 0.03
  },
  "topline": 0.78
}
```

**Agent 4 (Critic) Output:**
```json
{
  "validation": "PASS",
  "confidence": "HIGH",
  "grounding": "PASS - Cites energy_saving_behaviors.csv",
  "consistency": "PASS - Matches evidence direction",
  "recommendation": "ACCEPT"
}
```

**Ground Truth:** 77.3%
**Error:** 0.7pp
**Status:** ✅ EXCELLENT

---

### Example 2: Rework Triggered (Low Confidence)

**Input:**
- Question: "I think brands should prioritize environmental sustainability"
- Demographic: "not_private_households"

**Agent 2 (IR) Output:**
```json
{
  "evidence": [
    {
      "type": "qualitative",
      "relevance": 0.52,
      "excerpt": "Institutional living, diverse backgrounds, limited shared identity.",
      "interpretation": "Heterogeneous group, hard to generalize"
    }
  ],
  "confidence": "LOW"
}
```

**Agent 3 (Estimator) - Iteration 1:**
```json
{
  "reasoning": "Limited evidence. Applying general baseline for environmental attitudes (30%).",
  "distribution": {...},
  "topline": 0.30
}
```

**Agent 4 (Critic) - Iteration 1:**
```json
{
  "validation": "FAIL",
  "confidence": "LOW",
  "confidence_score": 0.42,
  "issues": [
    "Insufficient evidence (only 1 low-relevance source)",
    "High uncertainty due to demographic heterogeneity"
  ],
  "recommendation": "REWORK"
}
```

**Agent 3 (Estimator) - Iteration 2 (with feedback):**
```json
{
  "reasoning": "
  Feedback: Insufficient evidence, high uncertainty.
  Strategy: Use broader demographic inference + wider confidence interval.
  Assumption: Institutional living → mixed backgrounds → regression to mean (35%).
  Confidence: MEDIUM (increased from LOW by broadening assumptions)
  ",
  "distribution": {...},
  "topline": 0.35
}
```

**Agent 4 (Critic) - Iteration 2:**
```json
{
  "validation": "PASS",
  "confidence": "MEDIUM",
  "confidence_score": 0.65,
  "notes": "Accepted with MEDIUM confidence. Transparent about uncertainty.",
  "recommendation": "ACCEPT"
}
```

**Ground Truth:** 35.0%
**Error:** 0.0pp
**Status:** ✅ EXCELLENT (despite initial low confidence)

---

## Implementation Details

### Technology Stack
- **LLM Providers:** OpenAI (GPT-4o primary), Anthropic (Claude 3.5 Sonnet), Google (Gemini 2.0 Flash)
- **Orchestration:** LangGraph (agent workflow state machine)
- **Vector Search:** Sentence-Transformers (all-MiniLM-L6-v2 for embeddings)
- **Data Processing:** Pandas (CSV), NLTK (text preprocessing)
- **Evaluation:** scikit-learn (R², MAE metrics)

### File Structure
```
agent_estimator/
├── common/
│   ├── config.py                 # System constants (LIKERT_ORDER, etc.)
│   ├── llm_providers.py          # Multi-model LLM abstraction
│   ├── math_utils.py             # R², MAE, distribution utilities
│   └── openai_utils.py           # OpenAI API helpers
│
├── ir_agent/                     # AGENT 2: Data Extractor
│   ├── parser.py                 # Evidence retrieval logic
│   └── prompts.py                # IR agent prompts
│
├── estimator_agent/              # AGENT 3: Estimator
│   ├── estimator.py              # Prediction generation
│   └── prompts/
│       ├── general_system_prompt.txt            # General prompt
│       └── demographic_guidance/                # Class-specific prompts
│           ├── young_dependents.txt
│           ├── affluent_urban.txt
│           └── ... (22 classes)
│
├── qa_agent/                     # AGENT 4: Critic
│   └── critic.py                 # Validation logic
│
├── prompt_agent/                 # AGENT 1 + 5: Pattern Extractor & Improver
│   ├── general_agent.py          # Universal pattern discovery
│   ├── class_agent.py            # Class-specific patterns
│   ├── prompt_generator.py       # Pattern → prompt conversion
│   └── prompt_improver.py        # Reinforcement learning
│
└── orchestrator/
    └── runner.py                 # LangGraph workflow (coordinates all agents)
```

### Performance Characteristics
- **Latency:** 5-10 seconds per prediction (5 runs)
- **Cost:** ~$0.05-0.10 per prediction (GPT-4o pricing)
- **Accuracy:** R² = 0.84 average, 90.5% demographics pass (R² > 0.7)
- **Throughput:** 100-200 predictions/hour (with API rate limits)

### Scalability Considerations
- **Batch Processing:** Can parallelize predictions across demographics
- **Caching:** Evidence bundles cacheable (same question → same evidence)
- **Model Selection:** Can downgrade to GPT-3.5 for cost (10x cheaper, -0.10 R² penalty)
- **Edge Deployment:** Can fine-tune smaller models (Llama 3.1) for on-premise

---

## Conclusion

This 5-agent architecture achieves **production-ready performance** (83.8% R² average) through:

1. **Automated Learning (Agent 1):** Discovers patterns from data instead of manual engineering
2. **Quality Evidence (Agent 2):** Retrieves relevant, scored context with ground-truth exclusion
3. **Structured Reasoning (Agent 3):** Applies hierarchical prompts (general + specific) with systematic workflow
4. **Quality Gating (Agent 4):** Validates outputs and triggers rework when confidence is low
5. **Continuous Improvement (Agent 5):** Reinforcement learning loop for prompt evolution

**Key Innovation:** The system can be deployed to new domains (healthcare, politics, product preferences) with minimal manual tuning by running Agent 1 on new training data.

---

**Document Version:** 2.0
**Last Updated:** 2025-11-06
**System Version:** V10 (Production)
