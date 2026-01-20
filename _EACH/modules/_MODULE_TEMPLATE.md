# Module Template Documentation

This guide explains how to create custom modules for the EWOKS system using JSON configuration files.

## Frontend vs Backend: The Complete Picture

The workflow is:

1. **JSON defines the form** - Specifies what fields users see and how they're validated
2. **User fills the form** - Selects options, enters values, uploads files
3. **Backend receives `selectedSettings`** - A dictionary of the user's choices
4. **You use `extractSetting()` to process values** - Extracts settings with automatic type conversion
5. **You implement module logic** - Process proteins based on the extracted settings
6. **Results are visualized** - The modified protein list becomes an SDS-PAGE image

**JSON configures the interface:**
- What form fields appear
- Validation rules (min/max, length, file type)
- Options and defaults
- Internal codes for backend logic

**Backend implements the processing:**
- Extract settings using `extractSetting()`
- Perform the actual computations
- Modify proteins using the `Protein` class
- Return the processed protein list

## extractSetting(): The Bridge Between JSON and Backend

The `extractSetting()` function extracts user choices from the form and automatically converts them to the correct Python type based on the field type you defined in JSON.

**Function signature:**
```python
extractSetting(settingName, moduleIdentifier, selectedSettings, moduleData)
```

**It returns different types based on your field's `formtype`:**
- `ChoiceField` → string (the internal code value)
- `MultipleChoiceField` → list of strings
- `DecimalField` → float
- `BooleanField` → boolean
- `CharField` → string
- `FileField` → string (file path)

**Example usage in your backend:**
```python
from utils.helperFunctions import extractSetting

def myModule(moduleIdentifier, selectedSettings, moduleData):
    # Extract user's choice - returns the internal code value
    cutoff_mode = extractSetting("My Cutoff Setting", moduleIdentifier, selectedSettings, moduleData)
    
    # Extract user's number - returns a float
    threshold = extractSetting("Threshold Value", moduleIdentifier, selectedSettings, moduleData)
    
    # Extract user's multiple selections - returns a list of strings
    targets = extractSetting("Target Proteins", moduleIdentifier, selectedSettings, moduleData)
    
    # Now use these values in your logic
    ...
```

**Why use extractSetting()?** It handles the extraction and type conversion automatically, so you don't have to manually look up values in nested dictionaries or worry about type casting.

## Module Structure

Every module is defined in a JSON file with the following top-level structure:

```json
{
  "module_name": {
    "id": "module_name",
    "title": "Display Title",
    "subtitle": "Brief description of what this module does",
    "icon": "icons/modules/your_icon.svg",
    "settings": {
      // Field definitions go here
    }
  }
}
```

### Required Module Properties

- **id**: Unique identifier for the module (must match the key name)
- **title**: Display name shown in the UI
- **subtitle**: Brief description of the module's purpose
- **icon**: Path to the module's icon (relative to static directory)
- **settings**: Object containing all form fields for module configuration

## Available Field Types

The JSON defines form field specifications that are automatically converted into interactive UI elements. Each field type is specified by the `formtype` property and supports different validation and configuration options.

### 1. ChoiceField (Dropdown)

Single selection dropdown menu. Users see friendly display names, but the backend receives internal code values.

**Required properties:**
- `formtype`: `"ChoiceField"`
- `options`: Object where keys are display names (shown to users) and values are internal codes (sent to backend)

**Optional properties:**
- `default`: Default selected option key (must match a key in options)
- `required`: Boolean indicating if field is required (default: true)

**How it works:**
1. Users see the **keys** as dropdown options (e.g., "Inside the range")
2. When selected, the backend receives the **value** (e.g., "inside")
3. You extract it with `extractSetting()`, which returns the internal code
4. Use this code to determine your backend logic

**Example:**
```json
"fractionation_method": {
  "formtype": "ChoiceField",
  "options": {
    "Inside the range": "inside",
    "Outside the range": "outside"
  },
  "default": "Inside the range",
  "required": true
}
```

**In your backend:**
```python
mode = extractSetting("fractionation_method", moduleIdentifier, selectedSettings, moduleData)
# mode will be either "inside" or "outside" (the internal code, not the display name)

if mode == "inside":
    # Keep proteins inside the range
    ...
elif mode == "outside":
    # Keep proteins outside the range
    ...
```

**Key point:** The value you put in the JSON (e.g., `"inside"`) is what `extractSetting()` returns, not the key.

---

### 2. MultipleChoiceField (Multi-select)

Allows users to select multiple options from a list. Backend receives a list of internal codes.

**Required properties:**
- `formtype`: `"MultipleChoiceField"`
- `options`: Object with display names as keys and internal codes as values

**Optional properties:**
- `default`: Array of default selected option keys
- `required`: Boolean indicating if field is required (default: true)

**How it works:**
1. Users see the keys as checkboxes and can select multiple items
2. The backend receives a **list of the internal code values**
3. `extractSetting()` returns this list automatically
4. Loop through the list to apply logic to each selected item

**Example:**
```json
"target_proteins": {
  "formtype": "MultipleChoiceField",
  "options": {
    "Albumin": "ALBU_HUMAN",
    "IgG1": "IGHG1_HUMAN",
    "IgG2": "IGHG2_HUMAN",
    "Transferrin": "TRNFR_HUMAN"
  },
  "default": ["ALBU_HUMAN"],
  "required": true
}
```

**In your backend:**
```python
targets = extractSetting("target_proteins", moduleIdentifier, selectedSettings, moduleData)
# targets is now a list, e.g., ["ALBU_HUMAN", "IGHG1_HUMAN"]

for target_code in targets:
    # Apply depletion or other logic to each target
    proteins = Protein.deplete_by_gene_group(target_code)
```

**Key point:** `extractSetting()` returns the values (internal codes), not the keys (display names), as a list.

---

### 3. DecimalField (Numeric Input)

Numeric input field for measurements, percentages, and other numerical parameters. Backend receives a float.

**Required properties:**
- `formtype`: `"DecimalField"`

**Optional properties:**
- `default`: Default numeric value (default: 0.0)
- `min`: Minimum allowed value (default: 0)
- `max`: Maximum allowed value (default: 100)
- `step`: UI increment step for spinners (default: 0.1)
- `decimal_places`: Number of decimal places for rounding (default: 2)
- `required`: Boolean indicating if field is required (default: true)

**How it works:**
1. User enters a number in the input field
2. Form validates it's between `min` and `max`
3. `extractSetting()` returns the value as a float, rounded to `decimal_places`
4. Use this numeric value in your calculations

**Example:**
```json
"depletion_percentage": {
  "formtype": "DecimalField",
  "default": 80.0,
  "min": 0.0,
  "max": 100.0,
  "step": 5.0,
  "decimal_places": 1,
  "required": true
}
```

**In your backend:**
```python
percentage = extractSetting("depletion_percentage", moduleIdentifier, selectedSettings, moduleData)
# percentage is now a float, e.g., 80.0

# Use it in your logic
depletion_factor = percentage / 100.0
for protein in Protein.getAllProteins():
    current_abundance = protein.get_abundance()
    protein.set_abundance(current_abundance * (1 - depletion_factor))
```

**Key point:** `extractSetting()` automatically converts the string input to a float.

---

### 4. BooleanField (Checkbox)

Checkbox for toggling true/false values. Backend receives a boolean.

**Required properties:**
- `formtype`: `"BooleanField"`

**Optional properties:**
- `default`: Boolean default value (true or false, default: false)

**How it works:**
1. Rendered as a checkbox in the UI
2. User checks or leaves unchecked
3. `extractSetting()` returns `True` if checked, `False` if unchecked
4. Use in conditional logic to enable/disable features

**Example:**
```json
"enable_advanced_mode": {
  "formtype": "BooleanField",
  "default": false
}
```

**In your backend:**
```python
use_advanced = extractSetting("enable_advanced_mode", moduleIdentifier, selectedSettings, moduleData)
# use_advanced is True or False

if use_advanced:
    threshold = extractSetting("custom_threshold", moduleIdentifier, selectedSettings, moduleData)
    # Apply custom logic with the threshold
else:
    # Use default behavior
    pass
```

**Key point:** `extractSetting()` returns a boolean value, making it easy to use in `if` statements.

---

### 5. CharField (Text Input)

Single-line text input field for short text entries. Backend receives a string.

**Required properties:**
- `formtype`: `"CharField"`

**Optional properties:**
- `default`: Default text value (default: empty string)
- `min_length`: Minimum character length validation
- `max_length`: Maximum character length validation
- `required`: Boolean indicating if field is required (default: true)
- `help_text`: Helper text displayed under the field

**How it works:**
1. User enters text in the input field
2. Form validates length constraints (min/max)
3. `extractSetting()` returns the entered text as a string
4. Use the string in your logic

**Example:**
```json
"description": {
  "formtype": "CharField",
  "default": "",
  "min_length": 3,
  "max_length": 200,
  "required": false,
  "help_text": "Optional description of your custom settings"
}
```

**In your backend:**
```python
desc = extractSetting("description", moduleIdentifier, selectedSettings, moduleData)
# desc is now a string, e.g., "My custom settings"

# Use it to log or identify results
print(f"Running module with settings: {desc}")
```

**Key point:** `extractSetting()` returns the text as a string, validated by frontend constraints but not further processed.

---

### 6. FileField (File Upload)

File upload input for accepting files. Backend receives the file path/identifier.

**Required properties:**
- `formtype`: `"FileField"`

**Optional properties:**
- `required`: Boolean indicating if field is required (default: true)

**How it works:**
1. User selects a file via the file picker (currently only `.fasta` files are accepted)
2. Form validates the file extension
3. `extractSetting()` returns the file path/identifier as a string
4. Use this path to read and process the file in your backend

**Example:**
```json
"protein_file": {
  "formtype": "FileField",
  "required": true
}
```

**In your backend:**
```python
file_path = extractSetting("protein_file", moduleIdentifier, selectedSettings, moduleData)
# file_path is a string pointing to the uploaded FASTA file

# Read and process the file
sequences = parseFasta(file_path)
Protein.deleteAllProteins()
proteins = [Protein(header, sequence) for header, sequence in sequences.items()]
```

**Key point:** `extractSetting()` returns the file path, allowing you to read and process the file in your backend logic.

## Common Patterns

### Pattern 1: Inside/Outside Selection

Many fractionation modules require choosing whether to keep proteins inside or outside a range:

```json
{
  "fractionation_mode": {
    "formtype": "ChoiceField",
    "options": {
      "Keep inside range (remove outside)": "inside",
      "Keep outside range (remove inside)": "outside"
    },
    "default": "Keep inside range (remove outside)",
    "required": true
  },
  "min_value": {
    "formtype": "DecimalField",
    "default": 0.0,
    "min": 0.0,
    "max": 1000.0,
    "step": 10.0
  },
  "max_value": {
    "formtype": "DecimalField",
    "default": 100.0,
    "min": 0.0,
    "max": 1000.0,
    "step": 10.0
  }
}
```

Your backend receives the mode choice and can apply different logic based on the selection.

### Pattern 2: Protein Selection via Multi-choice

When users need to select specific proteins to target:

```json
{
  "target_proteins": {
    "formtype": "MultipleChoiceField",
    "options": {
      "Albumin": "ALBU_HUMAN",
      "Immunoglobulin G1": "IGHG1_HUMAN",
      "Transferrin": "TRNFR_HUMAN"
    },
    "default": ["ALBU_HUMAN"],
    "required": true
  },
  "depletion_level": {
    "formtype": "DecimalField",
    "default": 95.0,
    "min": 0.0,
    "max": 100.0,
    "step": 1.0,
    "decimal_places": 1
  }
}
```

Backend receives the list of protein codes and applies depletion logic to each.

### Pattern 3: Optional Advanced Settings

Allow users to enable detailed configuration:

```json
{
  "use_advanced_settings": {
    "formtype": "BooleanField",
    "default": false
  },
  "custom_threshold": {
    "formtype": "DecimalField",
    "default": 50.0,
    "min": 0.0,
    "max": 100.0
  }
}
```

Backend checks the boolean to determine whether to use default or custom parameters.

---

## Complete Example

See `example.json` in this directory for a working example that demonstrates all field types.
> example.json only demonstrates all the different field types. It does not perform any operations on the proteins.

## Data Flow: From JSON to Backend Processing

Understanding the complete workflow helps you design your modules correctly:

1. **JSON Definition**: You define form fields with `formtype`, options, defaults, and validation rules
2. **Form Rendering**: The system reads your JSON and creates interactive form fields on the web interface
3. **User Interaction**: User fills out the form with their choices
4. **Form Submission**: User clicks submit
5. **Form Validation**: Frontend validates based on your JSON constraints (min/max, length, required, etc.)
6. **Data Extraction**: Form values are collected into a dictionary called `selectedSettings`
7. **Backend Function Call**: Your module function receives `selectedSettings` along with `moduleIdentifier` and `moduleData`
8. **extractSetting() Usage**: You call `extractSetting()` for each setting you defined in JSON
9. **Type Conversion**: `extractSetting()` automatically converts the value to the correct Python type based on `formtype`
10. **Processing**: You use the extracted values to modify proteins via the `Protein` class
11. **Visualization**: Your processed protein list is visualized as an SDS-PAGE image

**Critical Points:**
- The **setting name** you use in `extractSetting()` must **exactly match** the key in your JSON settings
- `extractSetting()` handles type conversion automatically based on your field's `formtype`
- For ChoiceField/MultipleChoiceField, `extractSetting()` returns the **value** (internal code), not the key (display name)
- Always import `extractSetting` from `utils.helperFunctions` in your module

---

## Creating Your Own Module

1. **Copy the template**: Start with `example.json` as a base
2. **Rename the file**: Use a descriptive name (e.g., `my_module.json`)
3. **Update the module ID**: Change both the top-level key and the `id` field (they must match)
4. **Set module metadata**: Update `title`, `subtitle`, and `icon` for display
5. **Define your settings**: Add field definitions for your module's configuration
6. **Implement backend logic**: Add a function in `modules.py` that processes the form data (see [BACKEND_REFERENCE.md](BACKEND_REFERENCE.md))
7. **Test your module**: Load it in the EWOKS interface to verify it works

---

## Tips and Best Practices

### Field Design
- **Descriptive names**: Use clear names for settings (e.g., `"minimum_weight_kda"` not `"min_w"`)
- **Sensible defaults**: Provide defaults that work for common use cases
- **Clear options**: Make ChoiceField options user-friendly and understandable
- **Validation**: Use min/max/length constraints to prevent invalid inputs early

### Frontend-Backend Alignment
- **Match field names**: If your JSON has `"protein_count"`, use exactly that in `selectedSettings`
- **Document expectations**: Add comments in your backend code explaining what each field should contain
- **Validate input**: Don't rely solely on frontend validation; add checks in your backend code
- **Type consistency**: Be aware of types (DecimalField returns float, CharField returns string, etc.)

### User Experience
- **Help text**: Use `help_text` in CharField to guide users
- **Reasonable ranges**: Set min/max values for DecimalField to match real-world data
- **Logical grouping**: Order fields in a way that makes sense for the workflow
- **Icons**: Use clear, descriptive icons that represent the module's function

---

## Error Messages

If you encounter issues:

1. **"Module key does not match module id field"**
   - Fix: The JSON object key must equal the module's `id` property
   - Example: `{"my_module": {"id": "my_module", ...}}`

2. **"Form field type was not found"**
   - Fix: Check your `formtype` spelling (case-sensitive)
   - Valid types: `ChoiceField`, `MultipleChoiceField`, `DecimalField`, `FileField`, `BooleanField`, `CharField`

3. **"Module is missing 'id' field"**
   - Fix: Ensure every module object has an `id` property

4. **"Module is missing 'settings' field"**
   - Fix: Ensure every module has a `settings` object (even if empty)

5. **Invalid JSON syntax**
   - Fix: Use a JSON validator tool to check for syntax errors (missing commas, brackets, etc.)

---

## Getting Help

If you encounter issues or have questions:
1. Check that your JSON syntax is valid (use a JSON validator tool)
2. Ensure all required properties are present for each field type
3. Verify file paths and references are correct
4. Consult the `example.json` file for working examples
5. Review [Protein Class Reference](protein_reference.md) to understand how to manipulate proteins
