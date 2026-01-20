from django import forms
from django.core.validators import FileExtensionValidator

def construct_form(module):
    form_fields = {}
    moduleId = module.get("id")
    if not moduleId:
        raise SyntaxError(f"Module is missing 'id' field. \n\n {module}")
    
    if not module.get("settings"):
        raise SyntaxError(f"Module {moduleId} is missing 'settings' field. \n\n {module}")
    
    for setting_name, settingAtributes in module["settings"].items():
        field_type = settingAtributes.get("formtype")
        if field_type == "ChoiceField":
            options_dict = settingAtributes.get("options", None)
            if options_dict is None:
                raise SyntaxError(f"Module {moduleId} setting '{setting_name}' is missing 'options' field required for ChoiceField.")
            choices = [(key, key) for key in options_dict.keys()]
            field = forms.ChoiceField(label=setting_name, choices=choices, required=settingAtributes.get("required", True), initial=settingAtributes.get("default", choices[0][0]), widget=forms.Select(attrs={"class": "form-control"}))
        elif field_type == "MultipleChoiceField":
            options_dict = settingAtributes.get("options", {})
            choices = [(key, key) for key in options_dict.keys()]
            field = forms.MultipleChoiceField(label=setting_name, choices=choices, required=settingAtributes.get("required", True), initial=settingAtributes.get("default", []), widget=forms.SelectMultiple(attrs={"class": "form-control"}))
        elif field_type == "DecimalField":
            field = forms.DecimalField(label=setting_name,
                                       min_value=settingAtributes.get("min",0),
                                       max_value=settingAtributes.get("max",100),
                                       decimal_places=settingAtributes.get("decimal_places",2),
                                       initial=settingAtributes.get("default",0.0),
                                       required=settingAtributes.get("required", True),
                                       #error_messages={'required': settingAtributes.get("onInvalid","Enter a valid number.")},
                                       widget=forms.NumberInput(attrs={
                                           "step": settingAtributes.get("step",0.1),
                                           "class": "form-control"
                                       }))
        elif field_type == "FileField":
            field = forms.FileField(label=setting_name, required=settingAtributes.get("required", True),validators=[FileExtensionValidator(allowed_extensions=["fasta"])], widget=forms.FileInput(attrs={"class": "form-control"}))
        elif field_type == "BooleanField":
            field = forms.BooleanField(label=setting_name, required=False, initial=settingAtributes.get("default", False), widget=forms.CheckboxInput(attrs={"class": "form-check-input", "style": "width: 20px; height: 20px; cursor: pointer;"}))
        elif field_type == "CharField":
            field = forms.CharField(label=setting_name, required=settingAtributes.get("required", True), initial=settingAtributes.get("default", ""), help_text=settingAtributes.get("help_text", ""),
                                    min_length=settingAtributes.get("min_length", None), max_length=settingAtributes.get("max_length", None), widget=forms.TextInput(attrs={"class": "form-control"}))
        else: 
            raise NotImplementedError(f"Form field type: {field_type} was not found. Perhaps it was misspelled possible choices are: ChoiceField, MultipleChoiceField, DecimalField, FileField, BooleanField, CharField.")

        form_fields[f"{moduleId}:{setting_name}"] = field
    
    return type('DynamicModuleSettingsForm', (forms.Form,), form_fields)
