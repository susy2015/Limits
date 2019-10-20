import os
import json

# json file with bkg predictions and signal yields
json_bkgPred = 'Datacards/setup/SUSYNano19/dc_BkgPred.json'
json_sigYields = 'Datacards/setup/SUSYNano19/dc_SigYields.json'
json_TTZPred = 'Datacards/setup/SUSYNano19/TTZ_pred.json'
json_RarePred = 'Datacards/setup/SUSYNano19/Rare_pred.json'

def write_json(data, filename='combine_bkgPred.json'):
    with open(filename,'w') as f:
    	json.dump(data, f, indent=2, ensure_ascii=False)

with open(json_bkgPred, "a+") as new:
    newData = json.load(new)

with open(json_TTZPred, "r") as ttz, open(json_RarePred, "r") as diboson:
    ttz_insert = json.load(ttz)
    diboson_insert = json.load(diboson)
    newData['yieldsMap'].update(ttz_insert)
    newData['yieldsMap'].update(diboson_insert)
write_json(newData)

