def extractSetting(settingName,moduleIdentifier,selectedSettings,moduleData):
    """
    Extract and convert a setting value from module data based on its field type.
    This function retrieves a setting from module configuration, validates its existence,
    and converts it to the appropriate Python type based on the field type definition.
    settingName : str
        The name of the setting to extract from the module's settings configuration.
    moduleIdentifier : str
        The unique identifier for the module containing the setting.
    selectedSettings : dict
        Dictionary containing the user-selected values for settings, keyed by setting name.
    moduleData : dict
        Dictionary containing module configurations with structure:
        {moduleIdentifier: {"settings": {settingName: {"formtype": str, ...}}}}
    Any
        The extracted setting value converted to the appropriate type:
        - ChoiceField: str (selected option value)
        - MultipleChoiceField: list (selected option values)
        - DecimalField: float
        - FileField: str (file path/identifier)
        - BooleanField: bool
        - CharField: str
        If the specified setting name is not found in the module's settings configuration.
        If the setting's field type is not supported or recognized.
    """
    currentModuleSettings = moduleData[moduleIdentifier]
    settingsList = currentModuleSettings["settings"].get(settingName,None)
    if settingsList is None:
        raise ValueError(f"Failed to extract settings for module {moduleIdentifier} Setting: '{settingName}'. It was not found within current module settings. Valid options are : {list(currentModuleSettings['settings'].keys())}")
    fieldType = settingsList.get("formtype",None)
    match fieldType:
        case "ChoiceField":
            return currentModuleSettings["settings"][settingName]["options"][selectedSettings[settingName]]
        case "MultipleChoiceField":
            return [currentModuleSettings["settings"][settingName]["options"][option] for option in selectedSettings[settingName]]
        case "DecimalField":
            return float(selectedSettings[settingName])
        case "FileField":
            return selectedSettings[settingName]
        case "BooleanField":
            return bool(selectedSettings.get(settingName,False))
        case "CharField":
            return str(selectedSettings[settingName])
        case _:
            raise NotImplementedError(f"Setting field type: {fieldType} was not found. Perhaps it was misspelled possible choices are: ChoiceField, MultipleChoiceField, DecimalField, FileField, BooleanField, CharField.")
    
