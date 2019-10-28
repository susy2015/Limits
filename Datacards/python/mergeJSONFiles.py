import os
import json

# json file with bkg predictions and signal yields
json_binMaps = 'Datacards/setup/SUSYNano19/dc_BkgPred_BinMaps_master.json'
json_bkgPred = 'Datacards/setup/SUSYNano19/dc_BkgPred.json'
json_TTZPred = 'Datacards/setup/SUSYNano19/TTZ_pred.json'
json_RarePred = 'Datacards/setup/SUSYNano19/Rare_pred.json'
json_zinvPred = 'Datacards/setup/SUSYNano19/zinv_yields.json'
json_qcdPred = 'Datacards/setup/SUSYNano19/qcd_BkgPred.json'

def write_json(data, filename='combine_bkgPred.json'):
    with open(filename,'w') as f:
    	json.dump(data, f, indent=2, ensure_ascii=False)

with open(json_bkgPred, "a+") as new:
    newData = json.load(new)

with open(json_TTZPred, "r") as ttz, open(json_RarePred, "r") as diboson, open(json_zinvPred, "r") as znunu, open(json_qcdPred, "r") as qcd, open(json_binMaps, "r") as binMaps:
    ttz_insert = json.load(ttz)
    diboson_insert = json.load(diboson)
    znunu_insert = json.load(znunu)
    qcd_insert = json.load(qcd)
    binMaps_insert = json.load(binMaps)
    newData['binMaps']['phocr'].update(binMaps_insert['binMaps']['phocr'])
    newData['yieldsMap'].update(ttz_insert)
    newData['yieldsMap'].update(diboson_insert)
    newData['yieldsMap'].update(znunu_insert['yieldsMap'])
    newData['yieldsMap'].update(qcd_insert['yieldsMap'])
write_json(newData)

