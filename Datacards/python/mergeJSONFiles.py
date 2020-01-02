import os
import json

# json file with bkg predictions and signal yields
json_binMaps = 'Datacards/setup/SUSYNano19/dc_BkgPred_BinMaps_master.json'
json_lepPred = 'Datacards/setup/SUSYNano19/ll_BkgPred_v2.json'
json_TTZPred = 'Datacards/setup/SUSYNano19/TTZ_pred.json'
json_RarePred = 'Datacards/setup/SUSYNano19/Rare_pred.json'
json_zinvPred = 'Datacards/setup/SUSYNano19/zinv_yields_Run2.json'
json_qcdPred = 'Datacards/setup/SUSYNano19/qcd_BkgPred.json'

def write_json(data, filename='combine_bkgPred.json'):
    with open(filename,'w') as f:
    	json.dump(data, f, indent=2, ensure_ascii=False)

with open(json_binMaps, "a+") as new:
    newData = json.load(new)

with open(json_TTZPred, "r") as ttz, open(json_RarePred, "r") as diboson, open(json_zinvPred, "r") as znunu, open(json_qcdPred, "r") as qcd, open(json_lepPred, "r") as lepcr:
    ttz_insert = json.load(ttz)
    diboson_insert = json.load(diboson)
    znunu_insert = json.load(znunu)
    qcd_insert = json.load(qcd)
    lep_insert = json.load(lepcr)
    newData['yieldsMap'].update(ttz_insert)
    newData['yieldsMap'].update(diboson_insert)
    newData['yieldsMap'].update(znunu_insert['yieldsMap'])
    newData['yieldsMap'].update(qcd_insert['yieldsMap'])
    newData['yieldsMap'].update(lep_insert['yieldsMap'])
write_json(newData)

