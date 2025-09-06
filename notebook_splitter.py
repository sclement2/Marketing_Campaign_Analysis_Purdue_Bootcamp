#!/usr/bin/env python3
"""
Comprehensive Jupyter Notebook Splitting Toolkit
Analyzes notebook structure and splits into logical segments
"""

import nbformat
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd

class NotebookAnalyzer:
    def __init__(self, notebook_path: str):
        self.notebook_path = Path(notebook_path)
        with open(notebook_path, 'r', encoding='utf-8') as f:
            self.notebook = nbformat.read(f, as_version=4)
        self.analysis = self._analyze_structure()
    
    def _analyze_structure(self) -> Dict:
        """Analyze notebook structure and content"""
        analysis = {
            'total_cells': len(self.notebook.cells),
            'cell_types': {},
            'sections': [],
            'imports': [],
            'data_operations': [],
            'visualizations': [],
            'modeling_operations': []
        }
        
        current_section = None
        cell_count = 0
        
        for idx, cell in enumerate(self.notebook.cells):
            # Count cell types
            cell_type = cell.cell_type
            analysis['cell_types'][cell_type] = analysis['cell_types'].get(cell_type, 0) + 1
            
            if cell_type == 'markdown' and cell.source:
                source = ''.join(cell.source) if isinstance(cell.source, list) else cell.source
                
                # Find markdown headers
                header_match = re.match(r'^(#{1,6})\s+(.+)', source, re.MULTILINE)
                if header_match:
                    # Save previous section
                    if current_section:
                        current_section['cell_count'] = cell_count
                        current_section['end_cell'] = idx - 1
                        analysis['sections'].append(current_section)
                    
                    # Start new section
                    level = len(header_match.group(1))
                    title = header_match.group(2).strip()
                    current_section = {
                        'level': level,
                        'title': title,
                        'start_cell': idx,
                        'cell_count': 0
                    }
                    cell_count = 0
            
            elif cell_type == 'code' and cell.source:
                source = ''.join(cell.source) if isinstance(cell.source, list) else cell.source
                
                # Analyze code content
                if re.search(r'^(import|from)\s+', source, re.MULTILINE):
                    analysis['imports'].append(idx)
                
                if re.search(r'(pd\.|df\.|DataFrame|read_csv|merge|groupby)', source):
                    analysis['data_operations'].append(idx)
                
                if re.search(r'(plt\.|sns\.|plotly|matplotlib|seaborn)', source):
                    analysis['visualizations'].append(idx)
                
                if re.search(r'(fit\(|predict\(|sklearn|model|train|cross_val)', source):
                    analysis['modeling_operations'].append(idx)
            
            cell_count += 1
        
        # Add final section
        if current_section:
            current_section['cell_count'] = cell_count
            current_section['end_cell'] = len(self.notebook.cells) - 1
            analysis['sections'].append(current_section)
        
        return analysis
    
    def suggest_splits(self) -> List[Dict]:
        """Suggest logical splitting points"""
        suggestions = []
        
        # Strategy 1: Split by major sections (level 1 and 2 headers)
        major_sections = [s for s in self.analysis['sections'] if s['level'] <= 2]
        
        if len(major_sections) > 1:
            for i, section in enumerate(major_sections):
                notebook_name = f"{i+1:02d}_{self._clean_filename(section['title'])}"
                suggestions.append({
                    'strategy': 'by_sections',
                    'notebook_name': notebook_name,
                    'start_cell': section['start_cell'],
                    'end_cell': section.get('end_cell', len(self.notebook.cells) - 1),
                    'title': section['title'],
                    'estimated_cells': section['cell_count'],
                    'description': f"Section: {section['title']}"
                })
        
        # Strategy 2: Functional splits (if no clear sections)
        if len(major_sections) <= 2:
            functional_splits = self._suggest_functional_splits()
            suggestions.extend(functional_splits)
        
        return suggestions
    
    def _suggest_functional_splits(self) -> List[Dict]:
        """Suggest splits based on code functionality"""
        splits = []
        
        # Find natural breakpoints
        import_cells = self.analysis['imports']
        data_cells = self.analysis['data_operations']
        viz_cells = self.analysis['visualizations']
        model_cells = self.analysis['modeling_operations']
        
        if len(import_cells) > 0 and len(data_cells) > 0:
            # Split 1: Data loading and exploration
            end_eda = min(len(self.notebook.cells) // 3, 
                         max(data_cells[:len(data_cells)//2]) if data_cells else 20)
            
            splits.append({
                'strategy': 'functional',
                'notebook_name': '01_data_exploration',
                'start_cell': 0,
                'end_cell': end_eda,
                'title': 'Data Exploration and EDA',
                'description': 'Data loading, cleaning, and exploratory analysis'
            })
            
            # Split 2: Feature engineering and preprocessing
            start_prep = end_eda + 1
            end_prep = min(len(self.notebook.cells) * 2 // 3,
                          model_cells[0] if model_cells else len(self.notebook.cells) - 1)
            
            splits.append({
                'strategy': 'functional',
                'notebook_name': '02_preprocessing',
                'start_cell': start_prep,
                'end_cell': end_prep,
                'title': 'Data Preprocessing and Feature Engineering',
                'description': 'Data cleaning, feature creation, and preparation'
            })
            
            # Split 3: Modeling and evaluation
            if model_cells:
                splits.append({
                    'strategy': 'functional',
                    'notebook_name': '03_modeling',
                    'start_cell': end_prep + 1,
                    'end_cell': len(self.notebook.cells) - 1,
                    'title': 'Modeling and Evaluation',
                    'description': 'Model training, evaluation, and results'
                })
        
        return splits
    
    def _clean_filename(self, title: str) -> str:
        """Convert title to clean filename"""
        # Remove special characters and convert to lowercase
        clean = re.sub(r'[^\w\s-]', '', title.lower())
        # Replace spaces and multiple dashes with single underscores
        clean = re.sub(r'[-\s]+', '_', clean)
        # Remove leading/trailing underscores
        clean = clean.strip('_')
        return clean[:50]  # Limit length
    
    def print_analysis(self):
        """Print detailed analysis of the notebook"""
        print(f"=== NOTEBOOK ANALYSIS: {self.notebook_path.name} ===")
        print(f"Total cells: {self.analysis['total_cells']}")
        print(f"Cell types: {self.analysis['cell_types']}")
        print(f"Sections found: {len(self.analysis['sections'])}")
        print(f"Import cells: {len(self.analysis['imports'])}")
        print(f"Data operation cells: {len(self.analysis['data_operations'])}")
        print(f"Visualization cells: {len(self.analysis['visualizations'])}")
        print(f"Modeling cells: {len(self.analysis['modeling_operations'])}")
        
        print("\n=== SECTIONS ===")
        for section in self.analysis['sections']:
            print(f"{'#' * section['level']} {section['title']} "
                  f"(cells {section['start_cell']}-{section.get('end_cell', '?')}, "
                  f"count: {section['cell_count']})")


class NotebookSplitter:
    def __init__(self, analyzer: NotebookAnalyzer):
        self.analyzer = analyzer
        self.notebook = analyzer.notebook
    
    def split_notebook(self, splits: List[Dict], output_dir: str = "split_notebooks"):
        """Split notebook according to provided splits"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Create shared utilities file
        self._create_utils_file(output_path)
        
        for split in splits:
            self._create_split_notebook(split, output_path)
        
        # Create master README
        self._create_readme(splits, output_path)
        
        print(f"\n✓ Notebook split into {len(splits)} parts in '{output_dir}' directory")
    
    def _create_split_notebook(self, split: Dict, output_path: Path):
        """Create individual split notebook"""
        # Create new notebook
        new_nb = nbformat.v4.new_notebook()
        
        # Add header cell
        header_cell = nbformat.v4.new_markdown_cell(
            f"# {split['title']}\n\n"
            f"{split.get('description', '')}\n\n"
            f"**Part of:** {self.analyzer.notebook_path.name}"
        )
        new_nb.cells.append(header_cell)
        
        # Add setup cell for non-first notebooks
        if split['start_cell'] > 0:
            setup_code = (
                "# Setup and data loading\n"
                "from utils import ProjectConfig, load_intermediate_results, save_intermediate_results\n"
                "import pandas as pd\n"
                "import numpy as np\n"
                "import matplotlib.pyplot as plt\n\n"
                "config = ProjectConfig()\n"
                "# Load data from previous notebook\n"
                "# df = load_intermediate_results('data_from_previous_step.pkl', config)\n"
            )
            setup_cell = nbformat.v4.new_code_cell(setup_code)
            new_nb.cells.append(setup_cell)
        
        # Copy cells from original notebook
        start_idx = split['start_cell']
        end_idx = split.get('end_cell', len(self.notebook.cells) - 1)
        
        for i in range(start_idx, min(end_idx + 1, len(self.notebook.cells))):
            new_nb.cells.append(self.notebook.cells[i])
        
        # Add save cell for non-last notebooks
        if end_idx < len(self.notebook.cells) - 1:
            save_code = (
                "\n# Save results for next notebook\n"
                "# save_intermediate_results(df_processed, 'processed_data.pkl', config)\n"
                "# save_intermediate_results(analysis_results, 'analysis_results.pkl', config)\n"
                "print('✓ Results saved for next notebook')"
            )
            save_cell = nbformat.v4.new_code_cell(save_code)
            new_nb.cells.append(save_cell)
        
        # Save notebook
        filename = f"{split['notebook_name']}.ipynb"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            nbformat.write(new_nb, f)
        
        print(f"Created: {filepath}")
    
    def _create_utils_file(self, output_path: Path):
        """Create utilities file for data sharing between notebooks"""
        utils_content = '''"""
Utilities for sharing data between notebook segments
"""
import pandas as pd
import numpy as np
import pickle
import os
from pathlib import Path

class ProjectConfig:
    """Centralized configuration for the project"""
    def __init__(self):
        self.data_dir = Path("data/")
        self.output_dir = Path("outputs/")
        self.figures_dir = Path("figures/")
        self.models_dir = Path("models/")
        
        # Create directories if they don't exist
        for dir_path in [self.data_dir, self.output_dir, 
                        self.figures_dir, self.models_dir]:
            dir_path.mkdir(exist_ok=True)

def save_intermediate_results(data, filename, config):
    """Save intermediate results between notebooks"""
    filepath = config.output_dir / filename
    
    if isinstance(data, pd.DataFrame):
        data.to_pickle(filepath)
    else:
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    print(f"Saved: {filepath}")
    return filepath

def load_intermediate_results(filename, config):
    """Load results from previous notebook"""
    filepath = config.output_dir / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    if filename.endswith('.pkl'):
        if 'df' in filename.lower() or 'data' in filename.lower():
            return pd.read_pickle(filepath)
        else:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
    
def list_available_results(config):
    """List all available intermediate results"""
    files = list(config.output_dir.glob("*.pkl"))
    if files:
        print("Available intermediate results:")
        for f in files:
            print(f"  - {f.name}")
    else:
        print("No intermediate results found")
    return files
'''
        
        utils_path = output_path / "utils.py"
        with open(utils_path, 'w', encoding='utf-8') as f:
            f.write(utils_content)
        
        print(f"Created utilities file: {utils_path}")
    
    def _create_readme(self, splits: List[Dict], output_path: Path):
        """Create README file explaining the notebook structure"""
        readme_content = f"""# Split Notebook Structure

Original notebook: `{self.analyzer.notebook_path.name}`
Split into {len(splits)} logical segments.

## Notebooks Overview

"""
        
        for i, split in enumerate(splits, 1):
            readme_content += f"""### {i}. {split['notebook_name']}.ipynb
**Title:** {split['title']}  
**Description:** {split.get('description', 'N/A')}  
**Cells:** {split.get('estimated_cells', 'Unknown')}  

"""
        
        readme_content += """## Usage Instructions

1. **Run notebooks in order** - Each notebook depends on outputs from previous ones
2. **Data flow** - Intermediate results are saved in `outputs/` directory
3. **Utilities** - Common functions are in `utils.py`

## Directory Structure
```
split_notebooks/
├── utils.py                 # Shared utilities
├── 01_*.ipynb              # First notebook
├── 02_*.ipynb              # Second notebook
├── ...                     # Additional notebooks
├── outputs/                # Intermediate results
├── figures/                # Generated plots
└── README.md              # This file
```

## Running All Notebooks
```bash
# Run all notebooks in sequence
for nb in *.ipynb; do jupyter nbconvert --to notebook --execute "$nb"; done
```
"""
        
        readme_path = output_path / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"Created README: {readme_path}")


def main():
    """Main function to analyze and split notebook"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python notebook_splitter.py <notebook_path>")
        sys.exit(1)
    
    notebook_path = sys.argv[1]
    
    if not os.path.exists(notebook_path):
        print(f"Error: Notebook file '{notebook_path}' not found")
        sys.exit(1)
    
    # Analyze notebook
    print("Analyzing notebook structure...")
    analyzer = NotebookAnalyzer(notebook_path)
    analyzer.print_analysis()
    
    # Get splitting suggestions
    print("\n" + "="*50)
    suggestions = analyzer.suggest_splits()
    
    if not suggestions:
        print("No clear splitting strategy found. Notebook may not need splitting.")
        return
    
    print(f"Found {len(suggestions)} suggested splits:")
    for i, split in enumerate(suggestions):
        print(f"{i+1}. {split['notebook_name']}: {split['title']}")
        print(f"   Cells: {split.get('start_cell', 0)}-{split.get('end_cell', '?')}")
        print(f"   Description: {split.get('description', 'N/A')}")
    
    # Ask user for confirmation
    response = input(f"\nProceed with splitting into {len(suggestions)} notebooks? (y/n): ")
    
    if response.lower() == 'y':
        splitter = NotebookSplitter(analyzer)
        splitter.split_notebook(suggestions)
    else:
        print("Splitting cancelled.")

if __name__ == "__main__":
    main()
