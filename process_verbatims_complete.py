"""
Comprehensive Verbatim Processing Pipeline
Processes Soap & Glory verbatim data following ACORN-style structure

Steps:
1. Inventory & tag sources (Jan24, FY25, FY26)
2. UK-only filtering with audit logs
3. Standardize column names (snake_case)
4. Clean & dedupe
5. PII scrubbing
6. Text normalization
7. Sentiment & text features
8. Create stable keys (respondent_id, concept_id)
9. Export to ACORN-style CSVs
10. QA checks
"""

import pandas as pd
import numpy as np
import os
import re
import hashlib
from pathlib import Path
from textblob import TextBlob
import warnings
warnings.filterwarnings('ignore')

# Configuration
BASE_DIR = r"C:\Users\d.zhang\Desktop\Experiments"
OUTPUT_DIR = os.path.join(BASE_DIR, "project_data", "verbatims_processed")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Verbatim files
VERBATIM_FILES = {
    'Jan24': "Witty Optimist_S&G Jan'24 Verbatims V2.xlsx",
    'FY25': 'Witty Optimist_S&G FY25 Verbatims V2.xlsx',
    'FY26': 'Witty Optimist_S&G FY26 Verbatims V2.xlsx',
}

# Structured data (already processed)
STRUCTURED_DATA = os.path.join(BASE_DIR, "project_data", "concept_test_processed", "concept_test_wide.csv")

# Audit log
audit_log = []


def log_audit(message, **kwargs):
    """Log audit information"""
    entry = {'message': message}
    entry.update(kwargs)
    audit_log.append(entry)
    print(f"  [AUDIT] {message}")


def slugify(text):
    """Convert text to slug format"""
    if pd.isna(text) or text == '':
        return None
    text = str(text).lower().strip()
    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text


def to_snake_case(col_name):
    """Convert column name to snake_case"""
    if pd.isna(col_name):
        return col_name
    col_name = str(col_name).strip()
    # Remove content in parentheses
    col_name = re.sub(r'\([^)]*\)', '', col_name)
    # Replace special chars
    col_name = re.sub(r'[-\s.:]+', '_', col_name)
    col_name = re.sub(r'_+', '_', col_name)
    return col_name.lower().strip('_')


def scrub_pii(text):
    """Remove PII from text"""
    if pd.isna(text) or text == '':
        return text

    text = str(text)

    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

    # Phone numbers (various formats)
    text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]', text)
    text = re.sub(r'\b\d{5}\s?\d{6}\b', '[PHONE]', text)

    # URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', text)
    text = re.sub(r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '[URL]', text)

    # Social media handles
    text = re.sub(r'@\w+', '[HANDLE]', text)

    # UK postcodes
    text = re.sub(r'\b[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}\b', '[POSTCODE]', text, flags=re.IGNORECASE)

    # Names after "my name is"
    text = re.sub(r'my name is\s+\w+', 'my name is [NAME]', text, flags=re.IGNORECASE)
    text = re.sub(r"i'm\s+\w+", "i'm [NAME]", text, flags=re.IGNORECASE)

    return text


def normalize_text(text):
    """Normalize text for analysis"""
    if pd.isna(text) or text == '':
        return ''

    text = str(text)

    # Lowercase
    text = text.lower()

    # Normalize quotes and dashes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('—', '-').replace('–', '-')

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def get_sentiment(text):
    """Get sentiment using TextBlob"""
    if pd.isna(text) or text == '' or len(text.strip()) < 3:
        return 0.0, 'neutral'

    try:
        blob = TextBlob(str(text))
        polarity = blob.sentiment.polarity

        # Classify
        if polarity > 0.1:
            label = 'positive'
        elif polarity < -0.1:
            label = 'negative'
        else:
            label = 'neutral'

        return polarity, label
    except:
        return 0.0, 'neutral'


def check_toxicity(text):
    """Simple toxicity check (keyword-based)"""
    if pd.isna(text) or text == '':
        return False

    text_lower = str(text).lower()

    # Simple toxic keywords
    toxic_words = ['hate', 'stupid', 'idiot', 'terrible', 'awful', 'disgusting', 'worst']

    return any(word in text_lower for word in toxic_words)


def generate_embedding_ref(text):
    """Generate a stable reference key for embeddings"""
    if pd.isna(text) or text == '':
        return None

    # Use hash as reference
    return hashlib.md5(str(text).encode('utf-8')).hexdigest()[:16]


def process_verbatim_file(file_path, wave):
    """Process a single verbatim file"""

    print(f"\n{'='*80}")
    print(f"Processing: {wave} - {os.path.basename(file_path)}")
    print('='*80)

    xl = pd.ExcelFile(file_path)
    log_audit(f"Opened file: {os.path.basename(file_path)}", wave=wave, sheets=len(xl.sheet_names))

    # Get UK sheets only
    uk_sheets = [s for s in xl.sheet_names if 'UK' in s.upper()]
    print(f"  - Found {len(uk_sheets)} UK sheets: {uk_sheets}")
    log_audit(f"UK sheets found", wave=wave, count=len(uk_sheets), sheets=uk_sheets)

    all_verbatims = []

    for sheet_name in uk_sheets:
        print(f"\n  Processing sheet: {sheet_name}")

        # Read sheet
        df = pd.read_excel(xl, sheet_name=sheet_name)
        initial_rows = len(df)

        log_audit(f"Sheet loaded: {sheet_name}", wave=wave, rows=initial_rows, cols=df.shape[1])

        # Determine question type from sheet name
        if 'like' in sheet_name.lower():
            question_code = 'LIKES'
            question_text = 'What did you like about this concept?'
        elif 'dislike' in sheet_name.lower():
            question_code = 'DISLIKES'
            question_text = 'What did you dislike about this concept?'
        elif 'range' in sheet_name.lower():
            question_code = 'RANGE'
            question_text = 'How does this concept fit with the Soap & Glory range?'
        else:
            question_code = 'OTHER'
            question_text = sheet_name

        # Each column is a concept
        for col_idx, concept_name_raw in enumerate(df.columns):
            concept_name_clean = re.sub(r'\s*:\s*\(.*?\)\s*.*', '', str(concept_name_raw)).strip()
            concept_id = slugify(concept_name_clean)

            # Each row is a verbatim from a different respondent
            for row_idx, verbatim_text in enumerate(df[concept_name_raw]):
                if pd.isna(verbatim_text) or str(verbatim_text).strip() == '':
                    continue

                # Fabricate respondent_id (stable within wave)
                respondent_id = f"{wave.lower()}_c{concept_id}_r{row_idx:04d}"

                all_verbatims.append({
                    'respondent_id': respondent_id,
                    'wave': wave,
                    'source_file': os.path.basename(file_path),
                    'sheet_name': sheet_name,
                    'concept_name': concept_name_clean,
                    'concept_id': concept_id,
                    'question_code': question_code,
                    'question_text': question_text,
                    'verbatim_text': str(verbatim_text),
                    'row_idx': row_idx,
                    'col_idx': col_idx,
                })

        print(f"    - Extracted {len([v for v in all_verbatims if v['sheet_name'] == sheet_name])} verbatims")

    df_verbatims = pd.DataFrame(all_verbatims)
    log_audit(f"Total verbatims extracted", wave=wave, count=len(df_verbatims))

    return df_verbatims


def enrich_verbatims(df):
    """Add text features and enrichments"""

    print(f"\n{'='*80}")
    print("ENRICHING VERBATIMS WITH TEXT FEATURES")
    print('='*80)

    # PII scrubbing
    print("\n[1/7] Scrubbing PII...")
    df['verbatim_text_scrubbed'] = df['verbatim_text'].apply(scrub_pii)
    pii_count = (df['verbatim_text'] != df['verbatim_text_scrubbed']).sum()
    print(f"  - PII removed from {pii_count} verbatims")
    log_audit("PII scrubbing", verbatims_affected=pii_count)

    # Text normalization
    print("\n[2/7] Normalizing text...")
    df['verbatim_text_clean'] = df['verbatim_text_scrubbed'].apply(normalize_text)

    # Sentiment analysis
    print("\n[3/7] Analyzing sentiment...")
    sentiment_results = df['verbatim_text_clean'].apply(get_sentiment)
    df['sentiment_polarity'] = sentiment_results.apply(lambda x: x[0])
    df['sentiment_label'] = sentiment_results.apply(lambda x: x[1])

    sentiment_dist = df['sentiment_label'].value_counts()
    print(f"  - Sentiment distribution: {sentiment_dist.to_dict()}")
    log_audit("Sentiment analysis", distribution=sentiment_dist.to_dict())

    # Toxicity check
    print("\n[4/7] Checking toxicity...")
    df['toxicity_flag'] = df['verbatim_text_clean'].apply(check_toxicity)
    toxic_count = df['toxicity_flag'].sum()
    print(f"  - Toxic verbatims flagged: {toxic_count}")
    log_audit("Toxicity check", toxic_count=toxic_count)

    # Length features
    print("\n[5/7] Computing length features...")
    df['length_chars'] = df['verbatim_text_clean'].str.len()
    df['length_tokens'] = df['verbatim_text_clean'].str.split().str.len()

    print(f"  - Mean length: {df['length_chars'].mean():.1f} chars, {df['length_tokens'].mean():.1f} tokens")

    # Embedding references
    print("\n[6/7] Generating embedding references...")
    df['embeddings_ref'] = df['verbatim_text_clean'].apply(generate_embedding_ref)

    # Topic labeling (simple keyword-based for now)
    print("\n[7/7] Assigning topic labels...")
    df['topic_label'] = 'general'

    # Simple topic detection
    def detect_topic(text):
        if pd.isna(text):
            return 'general'
        text_lower = text.lower()

        if any(word in text_lower for word in ['price', 'expensive', 'cheap', 'cost', 'value']):
            return 'price'
        elif any(word in text_lower for word in ['smell', 'scent', 'fragrance', 'perfume']):
            return 'scent'
        elif any(word in text_lower for word in ['packaging', 'package', 'bottle', 'design']):
            return 'packaging'
        elif any(word in text_lower for word in ['skin', 'moisturise', 'hydrate', 'dry']):
            return 'skincare'
        elif any(word in text_lower for word in ['ingredient', 'natural', 'vegan', 'chemical']):
            return 'ingredients'
        elif any(word in text_lower for word in ['brand', 'soap & glory', 'soap and glory']):
            return 'brand'
        else:
            return 'general'

    df['topic_label'] = df['verbatim_text_clean'].apply(detect_topic)

    topic_dist = df['topic_label'].value_counts()
    print(f"  - Topic distribution: {topic_dist.to_dict()}")
    log_audit("Topic labeling", distribution=topic_dist.to_dict())

    return df


def create_respondents_table(df_verbatims):
    """Create respondents.csv (one row per respondent per wave)"""

    print(f"\n{'='*80}")
    print("CREATING RESPONDENTS TABLE")
    print('='*80)

    # Group by respondent
    respondents = df_verbatims.groupby('respondent_id').first()[['wave', 'source_file']].reset_index()

    # Add placeholder demographics (not available in verbatim data)
    respondents['region'] = 'UK'
    respondents['age'] = np.nan
    respondents['gender'] = np.nan
    respondents['acorn_group'] = np.nan

    print(f"  - Total respondents: {len(respondents)}")
    print(f"  - By wave: {respondents['wave'].value_counts().to_dict()}")
    log_audit("Respondents table created", count=len(respondents), by_wave=respondents['wave'].value_counts().to_dict())

    return respondents


def create_verbatims_table(df_verbatims):
    """Create verbatims.csv (one row per verbatim)"""

    print(f"\n{'='*80}")
    print("CREATING VERBATIMS TABLE")
    print('='*80)

    # Select columns for export
    columns = [
        'respondent_id',
        'wave',
        'concept_id',
        'concept_name',
        'question_code',
        'question_text',
        'verbatim_text',
        'verbatim_text_clean',
        'sentiment_polarity',
        'sentiment_label',
        'toxicity_flag',
        'length_chars',
        'length_tokens',
        'topic_label',
        'embeddings_ref',
        'source_file',
    ]

    df_export = df_verbatims[columns].copy()

    print(f"  - Total verbatims: {len(df_export)}")
    print(f"  - Unique concepts: {df_export['concept_id'].nunique()}")
    print(f"  - By wave: {df_export['wave'].value_counts().to_dict()}")

    log_audit("Verbatims table created",
              count=len(df_export),
              concepts=df_export['concept_id'].nunique(),
              by_wave=df_export['wave'].value_counts().to_dict())

    return df_export


def create_concept_metrics_table(df_verbatims):
    """Create concept_metrics.csv (aggregates per concept)"""

    print(f"\n{'='*80}")
    print("CREATING CONCEPT METRICS TABLE")
    print('='*80)

    # Aggregate by wave and concept
    metrics = df_verbatims.groupby(['wave', 'concept_id', 'concept_name']).agg({
        'respondent_id': 'nunique',
        'sentiment_polarity': ['mean', 'std'],
        'length_tokens': ['mean', 'std'],
        'toxicity_flag': 'sum',
    }).reset_index()

    # Flatten column names
    metrics.columns = [
        'wave', 'concept_id', 'concept_name',
        'n_respondents',
        'sentiment_mean', 'sentiment_std',
        'length_tokens_mean', 'length_tokens_std',
        'toxic_count'
    ]

    # Calculate sentiment distribution per concept
    sentiment_pct = df_verbatims.groupby(['wave', 'concept_id', 'sentiment_label']).size().unstack(fill_value=0)
    sentiment_pct = sentiment_pct.div(sentiment_pct.sum(axis=1), axis=0) * 100

    if 'positive' in sentiment_pct.columns:
        metrics = metrics.merge(
            sentiment_pct[['positive', 'negative', 'neutral']].reset_index(),
            on=['wave', 'concept_id'],
            how='left'
        )
        metrics.rename(columns={
            'positive': 'sentiment_positive_pct',
            'negative': 'sentiment_negative_pct',
            'neutral': 'sentiment_neutral_pct'
        }, inplace=True)

    print(f"  - Total concept-wave combinations: {len(metrics)}")
    log_audit("Concept metrics created", count=len(metrics))

    return metrics


def run_qa_checks(df_verbatims, df_respondents, df_concept_metrics):
    """Run QA checks and generate report"""

    print(f"\n{'='*80}")
    print("QA CHECKS")
    print('='*80)

    qa_results = {}

    # Row counts
    print("\n[CHECK 1] Row counts")
    qa_results['verbatims_count'] = len(df_verbatims)
    qa_results['respondents_count'] = len(df_respondents)
    qa_results['concepts_count'] = df_verbatims['concept_id'].nunique()
    print(f"  - Verbatims: {qa_results['verbatims_count']}")
    print(f"  - Respondents: {qa_results['respondents_count']}")
    print(f"  - Unique concepts: {qa_results['concepts_count']}")

    # Missing data
    print("\n[CHECK 2] Missing data")
    missing = df_verbatims[['verbatim_text', 'concept_id', 'question_code']].isnull().sum()
    print(f"  - Missing verbatim_text: {missing['verbatim_text']}")
    print(f"  - Missing concept_id: {missing['concept_id']}")
    qa_results['missing_verbatim_text'] = int(missing['verbatim_text'])

    # Distribution checks
    print("\n[CHECK 3] Distribution checks")
    print(f"  - Sentiment polarity range: [{df_verbatims['sentiment_polarity'].min():.2f}, {df_verbatims['sentiment_polarity'].max():.2f}]")
    print(f"  - Length range: {df_verbatims['length_chars'].min()}-{df_verbatims['length_chars'].max()} chars")

    # Top concepts
    print("\n[CHECK 4] Top 5 concepts by verbatim count")
    top_concepts = df_verbatims['concept_id'].value_counts().head(5)
    for concept, count in top_concepts.items():
        print(f"  - {concept}: {count} verbatims")

    qa_results['top_concepts'] = top_concepts.to_dict()

    # Wave coverage
    print("\n[CHECK 5] Wave coverage")
    wave_coverage = df_verbatims.groupby('wave')['concept_id'].nunique()
    for wave, count in wave_coverage.items():
        print(f"  - {wave}: {count} concepts")

    qa_results['wave_coverage'] = wave_coverage.to_dict()

    return qa_results


def save_outputs(df_verbatims, df_respondents, df_concept_metrics, qa_results):
    """Save all output files"""

    print(f"\n{'='*80}")
    print("SAVING OUTPUTS")
    print('='*80)

    # Save verbatims.csv
    verbatims_path = os.path.join(OUTPUT_DIR, "verbatims.csv")
    df_verbatims_export = create_verbatims_table(df_verbatims)
    df_verbatims_export.to_csv(verbatims_path, index=False, encoding='utf-8')
    print(f"\n[1/5] Saved: {verbatims_path}")
    print(f"      Shape: {df_verbatims_export.shape}")

    # Save respondents.csv
    respondents_path = os.path.join(OUTPUT_DIR, "respondents.csv")
    df_respondents.to_csv(respondents_path, index=False, encoding='utf-8')
    print(f"\n[2/5] Saved: {respondents_path}")
    print(f"      Shape: {df_respondents.shape}")

    # Save concept_metrics.csv
    metrics_path = os.path.join(OUTPUT_DIR, "concept_metrics.csv")
    df_concept_metrics.to_csv(metrics_path, index=False, encoding='utf-8')
    print(f"\n[3/5] Saved: {metrics_path}")
    print(f"      Shape: {df_concept_metrics.shape}")

    # Save audit log
    audit_path = os.path.join(OUTPUT_DIR, "audit_log.csv")
    pd.DataFrame(audit_log).to_csv(audit_path, index=False, encoding='utf-8')
    print(f"\n[4/5] Saved: {audit_path}")
    print(f"      Entries: {len(audit_log)}")

    # Save QA report
    qa_path = os.path.join(OUTPUT_DIR, "QA_REPORT.txt")
    with open(qa_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("VERBATIM PROCESSING - QA REPORT\n")
        f.write("="*80 + "\n\n")

        f.write("SUMMARY\n")
        f.write("-"*80 + "\n")
        f.write(f"Total verbatims: {qa_results['verbatims_count']}\n")
        f.write(f"Total respondents: {qa_results['respondents_count']}\n")
        f.write(f"Unique concepts: {qa_results['concepts_count']}\n\n")

        f.write("WAVE COVERAGE\n")
        f.write("-"*80 + "\n")
        for wave, count in qa_results['wave_coverage'].items():
            f.write(f"  {wave}: {count} concepts\n")

        f.write("\nTOP CONCEPTS\n")
        f.write("-"*80 + "\n")
        for concept, count in qa_results['top_concepts'].items():
            f.write(f"  {concept}: {count} verbatims\n")

    print(f"\n[5/5] Saved: {qa_path}")

    print("\n" + "="*80)
    print("PROCESSING COMPLETE!")
    print("="*80)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"\nFiles created:")
    print(f"  1. verbatims.csv - All verbatim responses with enrichments")
    print(f"  2. respondents.csv - Respondent-level data")
    print(f"  3. concept_metrics.csv - Concept-level aggregates")
    print(f"  4. audit_log.csv - Processing audit trail")
    print(f"  5. QA_REPORT.txt - Quality assurance summary")
    print("\n" + "="*80 + "\n")


def main():
    """Main processing pipeline"""

    print("\n" + "="*80)
    print("VERBATIM PROCESSING PIPELINE - START")
    print("="*80 + "\n")

    all_verbatims = []

    # Process each verbatim file
    for wave, filename in VERBATIM_FILES.items():
        file_path = os.path.join(BASE_DIR, filename)

        if not os.path.exists(file_path):
            print(f"WARNING: File not found: {filename}")
            log_audit(f"File not found", wave=wave, file=filename)
            continue

        df_wave = process_verbatim_file(file_path, wave)
        all_verbatims.append(df_wave)

    # Combine all verbatims
    print(f"\n{'='*80}")
    print("COMBINING ALL VERBATIMS")
    print('='*80)

    df_all = pd.concat(all_verbatims, ignore_index=True)
    print(f"\n  - Total verbatims combined: {len(df_all)}")
    print(f"  - Unique concepts: {df_all['concept_id'].nunique()}")
    print(f"  - By wave: {df_all['wave'].value_counts().to_dict()}")

    log_audit("Combined all verbatims",
              total=len(df_all),
              concepts=df_all['concept_id'].nunique(),
              by_wave=df_all['wave'].value_counts().to_dict())

    # Dedupe
    print(f"\n{'='*80}")
    print("DEDUPLICATING")
    print('='*80)

    initial_count = len(df_all)
    df_all = df_all.drop_duplicates(subset=['respondent_id', 'concept_id', 'question_code', 'verbatim_text'])
    final_count = len(df_all)
    dupes_removed = initial_count - final_count

    print(f"  - Duplicates removed: {dupes_removed}")
    log_audit("Deduplication", initial=initial_count, final=final_count, removed=dupes_removed)

    # Enrich verbatims
    df_all = enrich_verbatims(df_all)

    # Create tables
    df_respondents = create_respondents_table(df_all)
    df_concept_metrics = create_concept_metrics_table(df_all)

    # QA checks
    qa_results = run_qa_checks(df_all, df_respondents, df_concept_metrics)

    # Save outputs
    save_outputs(df_all, df_respondents, df_concept_metrics, qa_results)


if __name__ == "__main__":
    main()
