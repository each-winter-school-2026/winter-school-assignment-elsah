import re
from sys import modules
from turtle import pos
from django.http import HttpResponse
from django.shortcuts import render
import json
from app.EWOKS_Interface.formConstructor import construct_form
from SDS.SDS_PAGE import getExampleSDS_PAGE,virtualSDSPage_2DGaussian,parseFasta
from _EACH.protein import Protein
from django.views.generic import TemplateView
from pathlib import Path
import base64
import _EACH.modules as EWOKS_modules
import os

# Create your views here.

class IndexView(TemplateView):
    def get(self, request):
        moduleCardContent = self.POSTGET_get_modules()
        img_path = Path('app/EWOKS_Interface/static/img/emptySDS.png')
        with open(img_path, 'rb') as img_file:
            emptySDS_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        cardsToRender = [next((card for card in moduleCardContent if card.get('id') == 'fasta_input'), None)]
        sdspageimg = [emptySDS_base64 for _ in cardsToRender]
        
        
        return render(request, 'EWOKS_main.html',
                    {'renderCards': cardsToRender, 'insertableModules': moduleCardContent, 'sdspageimg': sdspageimg})
        

    
    def post(self, request):
        moduleOrder, instanceTypes, instanceSettings = self.POST_extract_module_settings(request)
        return self.POST_render_result(request, moduleOrder, instanceTypes, instanceSettings)
    
    def POST_render_result(self, request, moduleOrder, instanceTypes, instanceSettings):
        sdsPageImages = []
        moduleData = getModulesDictFromJsonFiles()

        cardsForRender = []

        # Run through instances in the selected order
        for instanceId in moduleOrder:
            module = instanceTypes.get(instanceId)
            if not module:
                continue
            settings = instanceSettings.get(instanceId, {})
            # Execute module
            sdsPageImgBase64 = EWOKS_modules.select(module, settings, moduleData)
            # Store a human-readable label for SEC
            column_label = None
            if module == "size_exclusion":
                column_label = settings.get("SEC column")

            
            if not sdsPageImgBase64:
                img_path = Path('app/EWOKS_Interface/static/img/sdsNoImgSupplied.png')
                with open(img_path, 'rb') as img_file:
                    sdsPageImgBase64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            sdsPageImages.append({
                "img": sdsPageImgBase64,
                "column_label": column_label
            })


            # Update defaults used to re-render the form
            for userSelectedSetting, selectedValue in settings.items():
                if userSelectedSetting in moduleData[module]["settings"]:
                    moduleData[module]["settings"][userSelectedSetting]["default"] = selectedValue

            # Build card object with form and instance id
            cardDef = dict(moduleData[module])
            cardDef['form'] = construct_form(module=cardDef)()
            cardDef['instance_id'] = instanceId
            cardsForRender.append(cardDef)

        return render(request, 'EWOKS_main.html',
                      {'renderCards': cardsForRender, 'sdspageimg': sdsPageImages, 'insertableModules': self.POSTGET_get_modules()})
    
    def POST_extract_module_settings(self, request):
        rawOrder = request.POST.get('module_order')
        moduleOrder = json.loads(rawOrder) if rawOrder else []

        instanceTypes = {}
        instanceSettings = {}
        # Walk all POST keys; expect names like "<instanceId>:<setting>" and "ModuleType:<instanceId>"
        for key, values in request.POST.lists():
            if key.startswith('ModuleType:'):
                instanceId = key.split(':', 1)[1]
                instanceTypes[instanceId] = values[0]
            elif ':' in key and not key.startswith(('Field:', 'ModuleType:')):
                instanceId, settingName = key.split(':', 1)
                if len(values) > 1:
                    instanceSettings.setdefault(instanceId, {})[settingName] = values
                else:
                    instanceSettings.setdefault(instanceId, {})[settingName] = values[0]
        return moduleOrder, instanceTypes, instanceSettings
    
    def POSTGET_get_modules(self):
        modules = getModulesDictFromJsonFiles()
        for moduleKey, moduleValues in modules.items():
            moduleValues['form'] = construct_form(module=moduleValues)()
            # seed instance id = module key for initial render
            moduleValues['instance_id'] = moduleKey
        
        moduleCardContent = modules.values()
        return moduleCardContent



def getModulesDictFromJsonFiles(moduleDirPath="_EACH/modules"):
    combinedModules = {}
    for moduleJsonFile in os.listdir(moduleDirPath):
        if not moduleJsonFile.endswith(".json"):
            continue
        with open(os.path.join(moduleDirPath,moduleJsonFile),'r') as f:
            moduleData = json.load(f)
            combinedModules.update(moduleData)
    for k,v in combinedModules.items():
        if k != v.get("id"):
            raise SyntaxError(f"Module key '{k}' does not match module 'id' field '{v.get('id')}'.")
    
    return combinedModules