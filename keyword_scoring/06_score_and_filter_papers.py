"""
Apply evidence-based keyword scoring to all papers
Easily adjustable for iteration
"""

from pathlib import Path
from typing import Dict, List, Tuple
import csv

# ============================================================================
# KEYWORD CONFIGURATION - EASY TO ADJUST
# ============================================================================

KEYWORDS = {
    # HIGH-VALUE METHODS (+5 points each)
    'methods': {
        'weight': 5,
        'keywords': [
            'delineat', 'management zone', 'zone delineation',
            'cluster', 'k-means', 'fuzzy c-means', 'hierarchical cluster',
            'classification', 'supervised', 'unsupervised',
            'machine learning', 'random forest', 'neural network', 'deep learning',
            'geostatistic', 'kriging', 'variogram',
            'principal component', 'pca',
            'segment', 'partition', 'stratif',
            'algorithm', 'optimization'
        ]
    },
    
    # HIGH-VALUE DATA (+4 points each)
    'data': {
        'weight': 4,
        'keywords': [
            'yield map', 'yield data', 'yield variability',
            'soil', 'soil property', 'soil variability',
            'electrical conductivity', 'ec map', 'apparent ec',
            'remote sensing', 'satellite', 'sentinel', 'landsat',
            'ndvi', 'vegetation index', 'multispectral',
            'uav', 'drone', 'unmanned aerial',
            'field study', 'field experiment', 'case study',
            'spatial variability', 'within-field variability'
        ]
    },
    
    # APPLICATION CONTEXT (+3 points each)
    'application': {
        'weight': 3,
        'keywords': [
            'precision agriculture', 'precision farming',
            'site-specific', 'site specific management',
            'variable rate', 'vra', 'vrt', 'variable rate application',
            'smart agriculture', 'smart farming'
        ]
    },
    
    # RESULTS/VALIDATION (+3 points each)
    'results': {
        'weight': 3,
        'keywords': [
            'validation', 'validate', 'accuracy', 'performance',
            'comparison', 'compar', 'evaluat', 'assess',
            'r2', 'rmse', 'correlation', 'coefficient',
            'improvement', 'optim', 'efficiency'
        ]
    },
    
    # GENERAL CONTEXT (+1 point each)
    'context': {
        'weight': 1,
        'keywords': [
            'crop', 'field', 'farm', 'agricultural',
            'sensor', 'mapping', 'spatial'
        ]
    },
    
    # EXCLUSION INDICATORS (-5 points each)
    'exclusion': {
        'weight': -5,
        'keywords': [
            'adoption study', 'farmer adoption', 'technology adoption',
            'economic analysis', 'cost-benefit', 'willingness to pay',
            'survey', 'questionnaire', 'interview',
            'iot only', 'internet of things', 'sensor network',
            'blockchain', 'policy', 'regulation',
            'social', 'perception', 'attitude'
        ]
    }
}

# Bonus for complete studies
BONUS_COMPLETE_STUDY = 5  # If has methods + data + results

# ============================================================================
# SCORING FUNCTIONS
# ============================================================================

def score_paper(paper: Dict) -> Tuple[float, Dict]:
    """Score a paper based on keywords"""
    
    title = paper.get('TI', '').lower()
    abstract = paper.get('AB', '').lower()
    text = f"{title} {abstract}"
    
    if len(abstract) < 100:
        return 0.0, {'reason': 'No abstract or too short'}
    
    score = 0.0
    details = {}
    
    # Score each category
    for category, config in KEYWORDS.items():
        category_score = 0
        keywords_found = []
        
        for keyword in config['keywords']:
            if keyword in text:
                category_score += config['weight']
                keywords_found.append(keyword)
                break  # Only count once per category
        
        details[f'{category}_score'] = category_score
        details[f'{category}_keywords'] = keywords_found
        score += category_score
    
    # Bonus for complete studies
    has_methods = details['methods_score'] > 0
    has_data = details['data_score'] > 0
    has_results = details['results_score'] > 0
    
    if has_methods and has_data and has_results:
        score += BONUS_COMPLETE_STUDY
        details['bonus'] = 'Complete study'
    
    details['total_score'] = score
    
    return score, details


def parse_ris_file(ris_file: Path) -> List[Dict]:
    """Parse RIS file"""
    papers = []
    current_paper = {}
    current_field = None
    current_value = []
    
    with open(ris_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if len(line) > 6 and line[2:6] == '  - ':
                if current_field and current_value:
                    value = ' '.join(current_value).strip()
                    if current_field in ['AU', 'N1']:
                        if current_field not in current_paper:
                            current_paper[current_field] = []
                        current_paper[current_field].append(value)
                    else:
                        current_paper[current_field] = value
                
                field_code = line[:2]
                field_value = line[6:].strip()
                
                if field_code == 'ER':
                    if current_paper:
                        papers.append(current_paper)
                    current_paper = {}
                    current_field = None
                    current_value = []
                else:
                    current_field = field_code
                    current_value = [field_value] if field_value else []
            
            elif current_field and line.strip():
                current_value.append(line.strip())
    
    return papers


def main():
    """Main execution"""
    
    input_file = Path('DB/FinalLibrary/FinalLibrary_Q1Only_WithAbstracts.ris')
    output_csv = Path('DB/FinalLibrary/Papers_Scored_EvidenceBased.csv')
    output_top = Path('DB/FinalLibrary/Top_Papers_ForScreening.csv')
    keywords_file = Path('DB/FinalLibrary/Keywords_Used.txt')
    
    print(f"\n{'='*80}")
    print(f"EVIDENCE-BASED KEYWORD SCORING")
    print(f"{'='*80}\n")
    
    # Save keywords used
    print(f"Saving keywords to: {keywords_file}")
    with open(keywords_file, 'w', encoding='utf-8') as f:
        f.write("KEYWORDS USED FOR SCORING\n")
        f.write("="*80 + "\n\n")
        f.write("Based on analysis of 250 randomly sampled abstracts\n\n\n")
        
        for category, config in KEYWORDS.items():
            label = category.upper()
            weight = config['weight']
            f.write(f"{label} (weight: {weight} points)\n")
            f.write("-"*40 + "\n")
            for i, keyword in enumerate(config['keywords'], 1):
                f.write(f"{i}. {keyword}\n")
            f.write("\n")
        
        f.write(f"BONUS: Complete study (methods + data + results): +{BONUS_COMPLETE_STUDY} points\n")
    
    print(f"✓ Keywords saved\n")
    
    # Read papers
    print(f"Reading papers from: {input_file}")
    papers = parse_ris_file(input_file)
    print(f"Total papers: {len(papers)}\n")
    
    # Score papers
    print(f"Scoring papers...")
    scored_papers = []
    
    for paper in papers:
        score, details = score_paper(paper)
        scored_papers.append({
            'paper': paper,
            'score': score,
            'details': details
        })
    
    # Sort by score
    scored_papers.sort(key=lambda x: x['score'], reverse=True)
    
    # Statistics
    scores = [sp['score'] for sp in scored_papers]
    
    print(f"\n{'='*80}")
    print(f"SCORING STATISTICS")
    print(f"{'='*80}\n")
    
    print(f"Total papers: {len(scored_papers)}")
    print(f"Score range: {min(scores):.1f} to {max(scores):.1f}")
    print(f"Mean score: {sum(scores)/len(scores):.1f}")
    print(f"Median score: {sorted(scores)[len(scores)//2]:.1f}")
    
    # Distribution
    high = sum(1 for s in scores if s >= 15)
    medium = sum(1 for s in scores if 10 <= s < 15)
    low = sum(1 for s in scores if 5 <= s < 10)
    very_low = sum(1 for s in scores if s < 5)
    
    print(f"\nScore distribution:")
    print(f"  High (≥15): {high} papers ({high/len(scores)*100:.1f}%)")
    print(f"  Medium (10-14): {medium} papers ({medium/len(scores)*100:.1f}%)")
    print(f"  Low (5-9): {low} papers ({low/len(scores)*100:.1f}%)")
    print(f"  Very low (<5): {very_low} papers ({very_low/len(scores)*100:.1f}%)")
    
    # Save all scored papers
    print(f"\n{'='*80}")
    print(f"SAVING RESULTS")
    print(f"{'='*80}\n")
    
    print(f"Writing all scored papers to: {output_csv}")
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Rank', 'Score', 'Title', 'Authors', 'Year', 'Journal', 'DOI',
                        'Methods Found', 'Data Found', 'Results Found', 'Exclusions'])
        
        for rank, sp in enumerate(scored_papers, 1):
            paper = sp['paper']
            details = sp['details']
            
            authors = paper.get('AU', [])
            if isinstance(authors, List):
                author_str = '; '.join(authors[:2])
                if len(authors) > 2:
                    author_str += ' et al.'
            else:
                author_str = str(authors) if authors else ''
            
            writer.writerow([
                rank,
                f"{sp['score']:.1f}",
                paper.get('TI', 'No title'),
                author_str,
                paper.get('PY', ''),
                paper.get('T2', ''),
                paper.get('DO', ''),
                ', '.join(details.get('methods_keywords', [])),
                ', '.join(details.get('data_keywords', [])),
                ', '.join(details.get('results_keywords', [])),
                ', '.join(details.get('exclusion_keywords', []))
            ])
    
    # Determine cutoff for top papers
    cutoff_score = 15
    top_papers = [sp for sp in scored_papers if sp['score'] >= cutoff_score]
    
    if len(top_papers) > 300:
        top_papers = scored_papers[:300]
        cutoff_score = top_papers[-1]['score']
    elif len(top_papers) < 200:
        top_papers = scored_papers[:200]
        cutoff_score = top_papers[-1]['score']
    
    # Save top papers for screening
    print(f"Writing top {len(top_papers)} papers to: {output_top}")
    with open(output_top, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Rank', 'Score', 'Title', 'Authors', 'Year', 'Journal', 'DOI',
                        'Abstract', 'Keywords Found', 'Decision', 'Notes'])
        
        for rank, sp in enumerate(top_papers, 1):
            paper = sp['paper']
            details = sp['details']
            
            authors = paper.get('AU', [])
            if isinstance(authors, List):
                author_str = '; '.join(authors[:2])
                if len(authors) > 2:
                    author_str += ' et al.'
            else:
                author_str = str(authors) if authors else ''
            
            # Combine all keywords found
            all_keywords = []
            for cat in ['methods', 'data', 'results', 'application']:
                all_keywords.extend(details.get(f'{cat}_keywords', []))
            
            writer.writerow([
                rank,
                f"{sp['score']:.1f}",
                paper.get('TI', 'No title'),
                author_str,
                paper.get('PY', ''),
                paper.get('T2', ''),
                paper.get('DO', ''),
                paper.get('AB', 'No abstract')[:300],
                ', '.join(all_keywords[:5]),
                '',
                ''
            ])
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"✓ All {len(scored_papers)} papers scored")
    print(f"✓ Top {len(top_papers)} papers selected for screening")
    print(f"  Score cutoff: {cutoff_score:.1f}")
    print(f"  Score range: {top_papers[-1]['score']:.1f} to {top_papers[0]['score']:.1f}")
    print(f"  Mean score: {sum(sp['score'] for sp in top_papers)/len(top_papers):.1f}")
    
    print(f"\n{'='*80}")
    print(f"FILES CREATED")
    print(f"{'='*80}\n")
    
    print(f"1. {output_csv}")
    print(f"   - All 1,038 papers with scores")
    print(f"   - Ranked from highest to lowest")
    
    print(f"\n2. {output_top}")
    print(f"   - Top {len(top_papers)} papers for manual screening")
    print(f"   - Includes abstract preview and space for decisions")
    
    print(f"\n3. {keywords_file}")
    print(f"   - Complete list of keywords used")
    print(f"   - For supplementary material")
    
    print(f"\n{'='*80}")
    print(f"NEXT STEPS")
    print(f"{'='*80}\n")
    
    print(f"1. Review top papers in: {output_top}")
    print(f"2. If keywords need adjustment:")
    print(f"   - Edit KEYWORDS dictionary in this script")
    print(f"   - Re-run: python Scripts/apply_keyword_scoring.py")
    print(f"   - Takes <1 minute to re-score all papers")
    print(f"3. Start manual screening when satisfied")
    
    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    main()
