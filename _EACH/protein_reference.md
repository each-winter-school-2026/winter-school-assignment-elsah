# Protein Class Reference

## Overview

The `Protein` class is the core data model for EWOKS, representing individual proteins with their sequences, physicochemical properties, and metadata. Each protein is automatically registered in a global registry and can be manipulated by modules throughout the workflow pipeline.

**Location:** [protein.py](protein.py)

**Related Documentation:**
- [HOW_TO_IMPLEMENT_A_MODULE.md](HOW_TO_IMPLEMENT_A_MODULE.md) - Step-by-step module creation guide
- [_MODULE_TEMPLATE.md](modules/_MODULE_TEMPLATE.md) - JSON module configuration reference

---

## Quick Start

```python
from _EACH.protein import Protein

# Create a protein instance (automatically registered)
header = ">sp|P02768|ALBU_HUMAN Albumin OS=Homo sapiens OX=9606 GN=ALB PE=1 SV=2 AB=40.0"
sequence = "MKWVTFISLLFLFSSAYSRGVFRR..."
protein = Protein(header, sequence)

# Access all proteins via global registry
all_proteins = Protein.getAllProteins()

# Modify protein abundance
protein.set_abundance(50.0)

# Use static methods for batch operations
Protein.fractionateProteinsByMolecularWeight("inside", minWeight=20, maxWeight=80)
```

---

## Architecture

### Global Registry Pattern

The `Protein` class maintains a class-level dictionary (`childClasses`) that automatically registers all protein instances. This eliminates the need to manually track protein objects across module executions.

**Key Benefits:**
- Access all proteins via `Protein.getAllProteins()`
- Batch operations work seamlessly across entire protein population  
- No explicit protein list passing between modules
- State persists throughout the workflow session

**Important Notes:**
- Registry persists for the Python process lifetime
- Use `Protein.deleteAllProteins()` to clear the registry when starting new workflows
- Each protein is keyed by its `entryName` (e.g., "ALBU_HUMAN")

---

## Class-Level Data

### Amino Acid Weight Table

```python
AMINO_ACID_WEIGHTS = {
    'A': 89.1, 'R': 174.2, 'N': 132.1, ...  # 20 canonical amino acids
    'U': 168.1, 'O': 255.3,                # Non-canonical
    'B': 132.6, 'Z': 146.65, ...           # Ambiguous codes (averages)
}
```

Used for molecular weight calculations. Includes support for ambiguous IUPAC codes.

### Kyte-Doolittle Hydrophobicity Scale

```python
AMINO_ACID_HYDROPHOBICITY = {
    "I": 4.5, "V": 4.2, "L": 3.8, ...  # Positive = hydrophobic
    "K": -3.9, "R": -4.5                # Negative = hydrophilic
}
```

Used for reversed phase chromatography simulations.

### Global Registry

```python
childClasses = {}  # {entryName: Protein instance}
masterProteomeID = None  # Set automatically when first protein is loaded
```

Automatically populated when proteins are instantiated.

---

## Static Methods (Module Helpers)

These methods are called by module implementations in [modules.py](modules.py) to perform batch operations on the protein population.

### `getAllProteins()` → list

Returns all proteins in the global registry as a list.

**Used by:** All modules (to pass proteins to SDS-PAGE visualization)

```python
proteins = Protein.getAllProteins()
```

---

### `deleteAllProteins()` → None

Clears the global registry and resets the proteome ID. Use this when starting a new workflow.

```python
Protein.deleteAllProteins()
```

---

### `fractionateProteinsByMolecularWeight(keepInsideOutsideSelection, minWeight=None, maxWeight=None)`

**Module:** `SDS_page_fractionation`

Filters proteins based on molecular weight with "inside" or "outside" window logic.

**Parameters:**
- `keepInsideOutsideSelection` (str): `"inside"` removes proteins *outside* the range; `"outside"` removes proteins *inside* the range
- `minWeight` (float, optional): Lower bound in kDa (default: -∞)
- `maxWeight` (float, optional): Upper bound in kDa (default: +∞)

**Logic:**
- `"inside"`: Sets `abundance = 0` for proteins < minWeight or > maxWeight
- `"outside"`: Sets `abundance = 0` for proteins within the window

**Example:**
```python
# Extract the 40-60 kDa fraction (deplete everything else)
Protein.fractionateProteinsByMolecularWeight("inside", minWeight=40, maxWeight=60)
```

---

### `fractionateProteinsByIsoelectricPoint(keepInsideOutsideSelection, minPI=None, maxPI=None)`

**Module:** `isoelectric_focussing`

Filters proteins based on isoelectric point (pI) with inside/outside logic.

**Parameters:**
- `keepInsideOutsideSelection` (str): `"inside"` or `"outside"` window selection
- `minPI` (float, optional): Lower pI bound (default: -∞)
- `maxPI` (float, optional): Upper pI bound (default: +∞)

**Example:**
```python
# Focus on acidic proteins (pI 4-6)
Protein.fractionateProteinsByIsoelectricPoint("inside", minPI=4.0, maxPI=6.0)
```

---

### `fractionateProteinsByHydrophobicity(keepInsideOutsideSelection, minHydrophobicity=None, maxHydrophobicity=None)`

**Module:** `reversed_phase_chromatography`

Separates proteins by average hydrophobicity using the Kyte-Doolittle scale.

**Parameters:**
- `keepInsideOutsideSelection` (str): `"inside"` or `"outside"` window selection
- `minHydrophobicity` (float, optional): Lower hydrophobicity bound (default: -∞)
- `maxHydrophobicity` (float, optional): Upper hydrophobicity bound (default: +∞)

**Note:** Hydrophobicity is the average Kyte-Doolittle value across all amino acids.

**Example:**
```python
# Elute hydrophobic proteins (positive hydrophobicity)
Protein.fractionateProteinsByHydrophobicity("inside", minHydrophobicity=0.5, maxHydrophobicity=3.0)
```

---

### `signalPeptideCleavage()` → None

**Module:** `signal_peptide_removal`

Cleaves signal peptides from proteins using the UniProt signal peptide database.

**Behavior:**
- Fetches signal peptide positions from `modules.signal.getSignalProteome()`
- For each protein with a known signal peptide, removes the N-terminal region
- Updates sequence, recalculates all properties, logs modification

**Database:** Uses the human proteome ID (UP000005640) by default, set via `masterProteomeID`

**Example:**
```python
Protein.signalPeptideCleavage()
# Automatically processes all proteins with known signal peptides
```

---

### `proteinImmunoaffinityDepletion(depletionDictionary)` → None

**Module:** `affinity_depletion`

Depletes protein abundance using immunoaffinity capture simulation.

**Parameters:**
- `depletionDictionary` (dict): Mapping of `{entryName: depletionFraction}`
  - `depletionFraction`: 0.0 (no depletion) to 1.0 (complete removal)

**Formula:** `new_abundance = old_abundance × (1 - depletionFraction)`

**Example:**
```python
# Remove 90% of albumin, 80% of immunoglobulins
Protein.proteinImmunoaffinityDepletion({
    "ALBU_HUMAN": 0.9,
    "IGHG1_HUMAN": 0.8
})
```

---

### `saveProteinsAsFasta(filepath, proteinList=None)` → None

Exports proteins to a FASTA file with full metadata.

**Parameters:**
- `filepath` (str): Output path (without `.fasta` extension)
- `proteinList` (list/dict, optional): Proteins to export (defaults to all in registry)

**Example:**
```python
Protein.saveProteinsAsFasta("output/processed_proteins")
# Creates: output/processed_proteins.fasta
```

---

## Instance Methods and Properties

### Constructor: `__init__(header, sequence)`

**Parameters:**
- `header` (str): FASTA header line (e.g., `>sp|P02768|ALBU_HUMAN ...`)
- `sequence` (str): Amino acid sequence

**Automatic Processing:**
1. Parses header to extract metadata
2. Converts sequence string to `Bio.Seq.Seq` object
3. Calculates molecular weight, hydrophobicity, and pI
4. Registers instance in `childClasses` using `entryName` as key
5. Initializes empty `modifications` list

**Example:**
```python
header = ">sp|P02768|ALBU_HUMAN Albumin OS=Homo sapiens OX=9606 GN=ALB PE=1 SV=2 AB=40.0"
sequence = "MKWVTFISLLFLFSSAYSRGVFRR..."
protein = Protein(header, sequence)
```

---

### Header Format and Parsing

Expected format: `>db|accession|entryName KEY=VALUE ...`

**Example:**
```
>sp|P02768|ALBU_HUMAN Albumin OS=Homo sapiens OX=9606 GN=ALB PE=1 SV=2 AB=40.0
```

**Parsed Fields:**
| Field | Example | Description |
|-------|---------|-------------|
| `db` | `sp` | Database (sp=SwissProt, tr=TrEMBL) |
| `accession` | `P02768` | UniProt accession number |
| `entryName` | `ALBU_HUMAN` | **Used as registry key** |
| `OX` | `9606` | Organism taxonomy ID (integer) |
| `GN` | `ALB` | Gene name |
| `PE` | `1` | Protein existence (1-5) |
| `SV` | `2` | Sequence version |
| `AB` | `40.0` | Initial abundance value |

**Special Handling:**
- If `OX=9606`, automatically sets `organism = "Homo Sapiens"`
- If no `AB` tag provided, defaults to 0.0

---

### Physicochemical Properties

#### `calculate_weight(sequence)` → float (kDa)

Calculates molecular weight using:
1. Sum of amino acid residue masses from `AMINO_ACID_WEIGHTS`
2. Subtract 18.0153 Da per peptide bond (water loss in condensation reactions)
3. Convert result to kilodaltons

**Precision:** Rounded to 3 decimal places

**Example:**
```python
weight = protein.get_weight()  # Returns float, e.g., 66.428 kDa
```

#### `calculate_hydrophobicity(sequence)` → float

Average Kyte-Doolittle hydrophobicity across all amino acids.
- **Positive values** (0.5 to 4.5) = hydrophobic
- **Negative values** (-4.5 to -0.5) = hydrophilic
- Used to simulate reversed phase chromatography

**Example:**
```python
hydro = protein.get_hydrophobicity()  # Returns float, e.g., -0.523
```

#### `calculate_isoelectric_point(sequence)` → float

Isoelectric point (pH at which protein has zero net charge).

Uses Biopython's `IsoelectricPoint.pi()` method, which solves the Henderson-Hasselbalch equation.
- Typical range: 4.0 to 9.0 for most proteins
- Used to simulate isoelectric focussing

**Example:**
```python
pI = protein.get_isoelectricpoint()  # Returns float, e.g., 5.134
```

---

### Instance Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `header` | str | Original FASTA header |
| `sequence` | Bio.Seq.Seq | Amino acid sequence |
| `weight` | float | Molecular weight in kDa |
| `hydrophobicity` | float | Average Kyte-Doolittle score |
| `isoelectric_point` | float | Calculated pI (isoelectric point) |
| `db` | str | Database identifier (sp, tr, etc.) |
| `accession` | str | UniProt accession |
| `entryName` | str | UniProt entry name (registry key) |
| `organism` | str | Organism name (if recognized) |
| `organismID` | int | NCBI taxonomy ID |
| `geneName` | str | Gene symbol |
| `proteinExistence` | int | PE level (1=protein exists, 5=inferred) |
| `sequenceVersion` | int | Sequence version |
| `abundance` | float | Relative abundance (0.0+) |
| `modifications` | list | Log of applied transformations |

---

### Getter Methods

All attributes have corresponding getter methods for safe access:

```python
protein.get_weight()            # Molecular weight (float)
protein.get_hydrophobicity()    # Hydrophobicity (float)
protein.get_isoelectricpoint()  # pI (float)
protein.get_sequence()          # Bio.Seq.Seq object
protein.get_entry_name()        # Entry name (string)
protein.get_accession()         # UniProt accession (string)
protein.get_gene_name()         # Gene name (string)
protein.get_abundance()         # Abundance value (float)
protein.get_sequence_length()   # Number of amino acids (int)
protein.get_db()                # Database (string)
protein.get_organism_id()       # Organism ID (int)
protein.get_protein_existence() # PE level (int)
```

---

### `set_abundance(abundance)` → None

Sets the protein's abundance value. Used by depletion modules.

```python
protein.set_abundance(50.0)
```

---

### `get_fasta()` → str

Generates a FASTA-formatted string for the protein, including all metadata and modification history.

**Output Format:**
```
>sp|P02768|ALBU_HUMAN proteinNamePlaceholder OS=Homo Sapiens OX=9606 GN=ALB PE=1 SV=2 AB=40.0 MD=False
MKWVTFISLLFLFSSAYSRGVFRRDAHKSEVAHRFKDLGEENFKALVLIAFAQYLQQCP
FEDHVKLVNEVTEFAKTCVADESAENCDKSLHTLFGDKLCTVATLRETYGEMADCCAKQ
```

**MD Tag:** Boolean indicating whether modifications have been applied (True if `modifications` list is non-empty)

**Sequence Wrapping:** Sequence is wrapped to 60 characters per line (standard FASTA format)

---

## Internal Methods (Private)

These are called automatically and should not be used directly from user code.

### `__processHeader()`

Parses the FASTA header and populates all metadata attributes. Called automatically during `__init__()`.

**Parses:**
- Database, accession, entry name (pipe-delimited)
- Organism ID, gene name, PE level, sequence version, abundance (from KEY=VALUE tags)

---

### `__cleaveSequence(startEnd, type="signal")`

Removes a region from the sequence (used by signal peptide removal).

**Parameters:**
- `startEnd`: Tuple of (start, end) indices (1-based, inclusive)
- `type`: Modification type label for logging

**Post-processing:**
- Calls `setSequenceDependentAttributes()` to recalculate weight, pI, hydrophobicity

---

### `setSequenceDependentAttributes()`

Recalculates weight, hydrophobicity, and pI after any sequence modification. **Must be called after sequence changes.**

---

## Workflow Integration

### Typical Module Pattern

Modules in [modules.py](modules.py) follow this pattern:

```python
from utils.helperFunctions import extractSetting

def my_module(moduleIdentifier, selectedSettings, moduleData):
    # 1. Extract settings from user input
    threshold = extractSetting("Threshold", moduleIdentifier, selectedSettings, moduleData)
    
    # 2. Call static Protein method for batch operation
    Protein.fractionateProteinsByMolecularWeight("inside", minWeight=threshold, maxWeight=100)
    
    # 3. Return all proteins for visualization
    return Protein.getAllProteins()
```

### Data Flow

1. **JSON Definition** - Module specifies form fields and constraints
2. **Form Rendering** - Web interface displays fields to user
3. **User Input** - User selects settings
4. **extractSetting()** - Retrieves and converts setting values
5. **Static Method** - Module calls Protein static method for batch operation
6. **Modification** - Proteins are mutated in-place (abundance set to 0 for depleted proteins)
7. **Visualization** - SDS-PAGE visualizer receives all proteins with current abundance values

---

## Key Design Patterns

### 1. Global Registry
- All proteins accessible via `Protein.childClasses` dictionary
- Simplifies cross-module state management
- Keyed by `entryName` for quick lookup

### 2. In-Place Modification
- Proteins are mutated directly (abundance changed, sequences cleaved)
- Modifications logged to `modifications` list for traceability
- Original data not preserved (consider filtering instead if you need to preserve state)

### 3. Abundance-Based Depletion
- Depletion sets `abundance = 0` rather than deleting protein objects
- Maintains consistent protein count across workflow
- SDS-PAGE visualization respects abundance (zero abundance = not visible)

### 4. Separation of Concerns
- **Static methods**: Batch operations (called by modules)
- **Instance methods**: Individual protein operations
- **Property calculations**: Physicochemical computations

---

## Usage Examples

### Loading Proteins from FASTA

```python
from SDS.SDS_PAGE import parseFasta
from _EACH.protein import Protein

# Clear any previous proteins
Protein.deleteAllProteins()

# Parse FASTA file and create Protein instances
# (returns dict of {entryName: Protein}, but proteins are also in registry)
sequences = parseFasta("data/proteomeHumanUniprot.fasta")

# Access all loaded proteins via registry
all_proteins = Protein.getAllProteins()
print(f"Loaded {len(all_proteins)} proteins")
```

### Applying Depletion

```python
# Deplete albumin and immunoglobulins
depletion_targets = {
    "ALBU_HUMAN": 0.95,    # Remove 95%
    "IGHG1_HUMAN": 0.85,   # Remove 85%
}

Protein.proteinImmunoaffinityDepletion(depletion_targets)

# Check result
albumin = Protein.childClasses.get("ALBU_HUMAN")
print(f"Albumin abundance after depletion: {albumin.get_abundance()}")
print(f"Modifications: {albumin.modifications}")
```

### Fractionation by pI

```python
# Extract acidic proteins (pI 4-6)
Protein.fractionateProteinsByIsoelectricPoint(
    keepInsideOutsideSelection="inside",
    minPI=4.0,
    maxPI=6.0
)

# Count remaining proteins
remaining = [p for p in Protein.getAllProteins() if p.get_abundance() > 0]
print(f"{len(remaining)} proteins in pI 4-6 range")
```

### Exporting Filtered Results

```python
# Export only proteins with non-zero abundance
active_proteins = [p for p in Protein.getAllProteins() if p.get_abundance() > 0]
Protein.saveProteinsAsFasta("output/filtered", proteinList=active_proteins)
```

---

## Important Notes

### Abundance Semantics

- `abundance = 0` means "depleted/removed" (not shown in SDS-PAGE visualization)
- Abundance values are **relative** (higher = more abundant)
- Typical range: 0.0 to 100.0 (from real plasma abundance data)

### Sequence Modifications

When sequences are modified (e.g., signal peptide cleavage):
1. Sequence is altered in the `sequence` attribute
2. `setSequenceDependentAttributes()` recalculates properties
3. Modification is logged in `modifications` list
4. Original sequence is **not** preserved

### Registry Persistence

- The `childClasses` registry persists for the lifetime of the Python process
- **Important:** If running multiple workflows, clear the registry:
  ```python
  Protein.deleteAllProteins()
  ```

### Memory Considerations

- All proteins remain in memory throughout the workflow
- For large proteomes (>100k proteins), monitor memory usage
- Consider filtering proteins early to reduce registry size

---

## Troubleshooting

### "KeyError: entryName not found in registry"

**Cause:** Protein not loaded or entry name doesn't match exact case
**Solution:** Verify FASTA header format and use `Protein.childClasses.keys()` to see available entry names

### "Abundance never changes after depletion"

**Cause:** Depletion dictionary key doesn't match protein's `entryName`
**Solution:** Print `Protein.childClasses.keys()` to verify exact entry names

### "Properties show old values after sequence modification"

**Cause:** `setSequenceDependentAttributes()` not called after sequence change
**Solution:** Always call this method after mutating the `sequence` attribute

### "Registry contains proteins from previous run"

**Cause:** Registry persists across runs in the same Python process
**Solution:** Call `Protein.deleteAllProteins()` before loading new data

---

## Related Files

- [modules.py](modules.py) - Module implementations that call Protein static methods
- [SDS/SDS_PAGE.py](../SDS/SDS_PAGE.py) - Visualization system that consumes Protein objects
- [modules/signal.py](../modules/signal.py) - Signal peptide database

---

**Last Updated:** January 2026  
**Maintained by:** EWOKS Development Team @ LUMC

**Last Updated:** January 2026  
**Maintained by:** EWOKS Development Team @ LUMC
