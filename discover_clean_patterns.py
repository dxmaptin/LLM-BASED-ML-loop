"""
Clean pattern discovery - NO TEST SET LEAKAGE.
Only analyzes CSV data, excluding the 10 holdout questions entirely.
"""

import pandas as pd
from pathlib import Path
import json
from agent_estimator.common.llm_providers import call_openai_api

# The 10 holdout questions that must be completely excluded
HOLDOUT_QUESTIONS = [
    "I think brands should consider environmental sustainability when putting on events",
    "Make an effort to cut down on the use of gas / electricity at home",
    "Fuel consumption is the most important feature when buying a new car",
    "I don't like the idea of being in debt",
    "I am very good at managing money",
    "It is important to be well insured for everything",
    "Healthy Eating",
    "Financial security after retirement is your own responsibility",
    "Switching utilities suppliers is well worth the effort",
    "I like to use cash when making purchases"
]


def load_all_acorn_training_data():
    """Load all ACORN CSV data, excluding the 10 holdout questions."""

    acorn_dir = Path("demographic_runs_ACORN")
    all_data = []

    print("\nLoading ACORN training data (excluding holdout questions)...")
    print("="*80)

    # Load each class
    for class_dir in acorn_dir.iterdir():
        if not class_dir.is_dir():
            continue

        csv_path = class_dir / "Flattened Data Inputs" / f"ACORN_{class_dir.name}.csv"
        if not csv_path.exists():
            continue

        print(f"Loading: {class_dir.name}")
        df = pd.read_csv(csv_path)

        # Filter out holdout questions
        before_count = len(df)
        df = df[~df['question'].isin(HOLDOUT_QUESTIONS)]
        after_count = len(df)

        if before_count > after_count:
            print(f"  Filtered out {before_count - after_count} holdout questions")

        df['class_name'] = class_dir.name
        all_data.append(df)

    combined = pd.concat(all_data, ignore_index=True)

    print("="*80)
    print(f"Total rows loaded: {len(combined)}")
    print(f"Unique questions: {combined['question'].nunique()}")
    print(f"Unique classes: {combined['class_name'].nunique()}")

    # Verify no holdout questions leaked
    leaked = [q for q in HOLDOUT_QUESTIONS if q in combined['question'].values]
    if leaked:
        raise ValueError(f"ERROR: Holdout questions found in training data: {leaked}")
    else:
        print("\n[OK] Verified: No holdout questions in training data")

    return combined


def discover_general_patterns(df):
    """
    Agent 1: Discover universal patterns across ALL demographics.
    Only uses training data - no knowledge of test set performance.
    """

    print("\n" + "="*80)
    print("AGENT 1: DISCOVERING GENERAL PATTERNS FROM TRAINING DATA")
    print("="*80)

    # Calculate overall statistics
    print("\nCalculating aggregate statistics...")

    question_stats = []

    for question in df['question'].unique():
        q_data = df[df['question'] == question]

        # Calculate average distribution across all classes
        avg_dist = {
            'strongly_agree': q_data['strongly_agree'].mean(),
            'slightly_agree': q_data['slightly_agree'].mean(),
            'neither_agree_nor_disagree': q_data['neither_agree_nor_disagree'].mean(),
            'slightly_disagree': q_data['slightly_disagree'].mean(),
            'strongly_disagree': q_data['strongly_disagree'].mean()
        }

        topline = avg_dist['strongly_agree'] + avg_dist['slightly_agree']
        std_dev = q_data['topline_percent'].std()

        question_stats.append({
            'question': question,
            'avg_topline': topline,
            'std_dev': std_dev,
            'num_classes': len(q_data),
            'distribution': avg_dist
        })

    stats_df = pd.DataFrame(question_stats)

    print(f"\nAnalyzed {len(stats_df)} unique questions")
    print(f"Average topline: {stats_df['avg_topline'].mean():.1f}%")
    print(f"Average std dev: {stats_df['std_dev'].mean():.1f}%")

    # Identify different types of questions by topline
    print("\nDistribution of agreement levels:")
    print(f"  Very Low (<30%): {(stats_df['avg_topline'] < 30).sum()} questions")
    print(f"  Low (30-40%): {((stats_df['avg_topline'] >= 30) & (stats_df['avg_topline'] < 40)).sum()} questions")
    print(f"  Medium (40-60%): {((stats_df['avg_topline'] >= 40) & (stats_df['avg_topline'] < 60)).sum()} questions")
    print(f"  High (60-70%): {((stats_df['avg_topline'] >= 60) & (stats_df['avg_topline'] < 70)).sum()} questions")
    print(f"  Very High (70%+): {(stats_df['avg_topline'] >= 70).sum()} questions")

    # Show top/bottom questions for pattern learning
    print("\n" + "-"*80)
    print("HIGHEST AGREEMENT QUESTIONS (top 10):")
    print("-"*80)
    top_10 = stats_df.nlargest(10, 'avg_topline')
    for idx, row in top_10.iterrows():
        print(f"{row['avg_topline']:.1f}% - {row['question'][:70]}")

    print("\n" + "-"*80)
    print("LOWEST AGREEMENT QUESTIONS (bottom 10):")
    print("-"*80)
    bottom_10 = stats_df.nsmallest(10, 'avg_topline')
    for idx, row in bottom_10.iterrows():
        print(f"{row['avg_topline']:.1f}% - {row['question'][:70]}")

    # Use LLM to analyze patterns
    print("\n" + "-"*80)
    print("Using LLM to identify behavioral patterns...")
    print("-"*80)

    # Prepare data for LLM
    high_questions = stats_df.nlargest(20, 'avg_topline')[['question', 'avg_topline']].to_dict('records')
    low_questions = stats_df.nsmallest(20, 'avg_topline')[['question', 'avg_topline']].to_dict('records')
    medium_questions = stats_df[(stats_df['avg_topline'] >= 40) & (stats_df['avg_topline'] <= 60)].nlargest(20, 'avg_topline')[['question', 'avg_topline']].to_dict('records')

    llm_prompt = f"""You are analyzing UK consumer survey data to discover universal behavioral patterns.

You have access to {len(stats_df)} questions with their average agreement rates across 22 demographic segments.

HIGH AGREEMENT QUESTIONS (60%+ agreement):
{json.dumps(high_questions, indent=2)}

LOW AGREEMENT QUESTIONS (<30% agreement):
{json.dumps(low_questions, indent=2)}

MEDIUM AGREEMENT QUESTIONS (40-60% agreement):
{json.dumps(medium_questions, indent=2)}

IMPORTANT: You have NOT seen test set results. You are only analyzing these training questions.

Your task: Identify general principles that explain these patterns:

1. What types of behaviors/attitudes get HIGH agreement (60%+)?
2. What types get LOW agreement (<30%)?
3. What types get MEDIUM agreement (40-60%)?
4. Are there patterns around:
   - Environmental topics?
   - Financial topics?
   - Health topics?
   - Digital/technology topics?
   - Aspirational vs actual behavior?
   - Convenience vs effort required?

Provide 10-15 general principles that could be used to predict NEW questions you've never seen.
Focus on the TYPE of question, not memorizing specific questions.

Format as JSON:
{{
  "general_principles": [
    {{"principle": "...", "reasoning": "...", "baseline_agreement": X}},
    ...
  ],
  "concept_type_baselines": {{
    "easy_behaviors": X,
    "difficult_behaviors": Y,
    "aspirational_attitudes": Z,
    "practical_attitudes": W
  }}
}}
"""

    response = call_openai_api(
        system_prompt="You are a data scientist specializing in consumer behavior patterns.",
        user_prompt=llm_prompt,
        model="gpt-4o",
        temperature=0.3,
        max_tokens=3000
    )

    try:
        patterns = json.loads(response.content)
        print("\n[OK] LLM identified patterns successfully")
        return {
            'question_stats': stats_df,
            'llm_patterns': patterns
        }
    except:
        print("\n[WARNING] Could not parse LLM response as JSON")
        print(response.content)
        return {
            'question_stats': stats_df,
            'llm_patterns': {'raw_response': response.content}
        }


def generate_clean_prompt(patterns):
    """Generate prompt from discovered patterns - no test set knowledge."""

    print("\n" + "="*80)
    print("GENERATING CLEAN PROMPT FROM PATTERNS")
    print("="*80)

    stats_df = patterns['question_stats']
    llm_patterns = patterns['llm_patterns']

    # Calculate baseline distributions by agreement level
    very_high = stats_df[stats_df['avg_topline'] >= 70]
    high = stats_df[(stats_df['avg_topline'] >= 60) & (stats_df['avg_topline'] < 70)]
    medium = stats_df[(stats_df['avg_topline'] >= 40) & (stats_df['avg_topline'] < 60)]
    low = stats_df[(stats_df['avg_topline'] >= 30) & (stats_df['avg_topline'] < 40)]
    very_low = stats_df[stats_df['avg_topline'] < 30]

    print(f"\nCalculating baseline distributions:")
    print(f"  Very High (70%+): {len(very_high)} questions")
    print(f"  High (60-70%): {len(high)} questions")
    print(f"  Medium (40-60%): {len(medium)} questions")
    print(f"  Low (30-40%): {len(low)} questions")
    print(f"  Very Low (<30%): {len(very_low)} questions")

    # Average distributions for each category
    def calc_avg_dist(subset):
        if len(subset) == 0:
            return None
        dists = []
        for _, row in subset.iterrows():
            dists.append(row['distribution'])

        avg = {
            'SA': sum(d['strongly_agree'] for d in dists) / len(dists),
            'A': sum(d['slightly_agree'] for d in dists) / len(dists),
            'N': sum(d['neither_agree_nor_disagree'] for d in dists) / len(dists),
            'D': sum(d['slightly_disagree'] for d in dists) / len(dists),
            'SD': sum(d['strongly_disagree'] for d in dists) / len(dists)
        }
        return avg

    dist_very_high = calc_avg_dist(very_high)
    dist_high = calc_avg_dist(high)
    dist_medium = calc_avg_dist(medium)
    dist_low = calc_avg_dist(low)
    dist_very_low = calc_avg_dist(very_low)

    # Generate prompt using LLM
    llm_prompt = f"""You are writing a system prompt for an LLM that predicts UK consumer attitudes and behaviors.

You have analyzed training data and discovered these patterns:

LEARNED PATTERNS:
{json.dumps(llm_patterns, indent=2)}

BASELINE DISTRIBUTIONS BY AGREEMENT LEVEL:

Very High Agreement (70%+): {len(very_high)} questions
Average distribution: SA {dist_very_high['SA']:.0f}%, A {dist_very_high['A']:.0f}%, N {dist_very_high['N']:.0f}%, D {dist_very_high['D']:.0f}%, SD {dist_very_high['SD']:.0f}%

High Agreement (60-70%): {len(high)} questions
Average distribution: SA {dist_high['SA']:.0f}%, A {dist_high['A']:.0f}%, N {dist_high['N']:.0f}%, D {dist_high['D']:.0f}%, SD {dist_high['SD']:.0f}%

Medium Agreement (40-60%): {len(medium)} questions
Average distribution: SA {dist_medium['SA']:.0f}%, A {dist_medium['A']:.0f}%, N {dist_medium['N']:.0f}%, D {dist_medium['D']:.0f}%, SD {dist_medium['SD']:.0f}%

Low Agreement (30-40%): {len(low)} questions
Average distribution: SA {dist_low['SA']:.0f}%, A {dist_low['A']:.0f}%, N {dist_low['N']:.0f}%, D {dist_low['D']:.0f}%, SD {dist_low['SD']:.0f}%

Very Low Agreement (<30%): {len(very_low)} questions
Average distribution: SA {dist_very_low['SA']:.0f}%, A {dist_very_low['A']:.0f}%, N {dist_very_low['N']:.0f}%, D {dist_very_low['D']:.0f}%, SD {dist_very_low['SD']:.0f}%

CRITICAL: Write a system prompt that uses these GENERAL PATTERNS to predict NEW questions.
DO NOT mention any specific training questions.
DO NOT encode memorized answers.

The prompt should:
1. Classify the concept type (easy behavior, difficult behavior, aspirational attitude, etc.)
2. Apply the appropriate baseline distribution
3. Adjust for demographic factors (age, income)
4. Respect proximal evidence from the evidence bundle
5. Output a 5-point Likert distribution

Format: Clear, structured instructions for an LLM. Include decision workflow and calibration rules.
"""

    response = call_openai_api(
        system_prompt="You are an expert prompt engineer.",
        user_prompt=llm_prompt,
        model="gpt-4o",
        temperature=0.2,
        max_tokens=4000
    )

    return response.content


def main():
    print("="*80)
    print("CLEAN PATTERN DISCOVERY - NO TEST SET LEAKAGE")
    print("="*80)
    print("\nThis script will:")
    print("1. Load all ACORN CSV data")
    print("2. EXCLUDE the 10 holdout questions completely")
    print("3. Discover patterns from remaining questions only")
    print("4. Generate a clean prompt with no test set knowledge")
    print("\n" + "="*80)

    # Load training data
    df = load_all_acorn_training_data()

    # Discover patterns
    patterns = discover_general_patterns(df)

    # Save patterns for inspection
    patterns_file = Path("clean_patterns_discovered.json")
    with open(patterns_file, 'w') as f:
        # Convert dataframe to dict for JSON serialization
        patterns_to_save = {
            'question_stats': patterns['question_stats'].to_dict('records'),
            'llm_patterns': patterns['llm_patterns']
        }
        json.dump(patterns_to_save, f, indent=2)
    print(f"\n[OK] Saved patterns to: {patterns_file}")

    # Generate prompt
    print("\n" + "="*80)
    print("Generating clean prompt...")
    print("="*80)

    prompt_text = generate_clean_prompt(patterns)

    # Save prompt
    prompt_file = Path("agent_estimator/estimator_agent/prompts/general_system_prompt_CLEAN.txt")
    prompt_file.write_text(prompt_text, encoding='utf-8')

    print(f"\n[OK] Generated clean prompt: {prompt_file}")
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Training questions analyzed: {patterns['question_stats']['question'].nunique()}")
    print(f"Holdout questions excluded: {len(HOLDOUT_QUESTIONS)}")
    print(f"Patterns discovered and saved: {patterns_file}")
    print(f"Clean prompt generated: {prompt_file}")
    print("\nNext step: Test this prompt on the 10 holdout questions")
    print("="*80)


if __name__ == "__main__":
    main()
