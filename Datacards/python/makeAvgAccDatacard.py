#! /usr/bin/python
import os
import argparse



def main() :
    parser = argparse.ArgumentParser(description='Take the average of PFMET and genMET and make datacards.')
    parser.add_argument("-i", "--inputdir", dest="inputdir", help="Input dir: PFMET.")
    parser.add_argument("-g", "--genmetdir", dest="genmetdir", help="Input dir: genMET.")
    parser.add_argument("-o", "--outdir", dest="outdir", help="Output dir.")
    args = parser.parse_args()

    pfMetDCDir = args.inputdir
    genMetDCDir = args.genmetdir
    outputDir = args.outdir

    for d in os.listdir(pfMetDCDir) :
        if '.' in d :
            continue
        print d
        if not os.path.exists(os.path.join(outputDir,d)) :
            os.makedirs(os.path.join(outputDir,d))
        for dc in os.listdir(os.path.join(pfMetDCDir,d)) :
            if not '.txt' in dc :
                continue
            print 'processing', dc
            makeNewDatacards(os.path.join(pfMetDCDir,d,dc), os.path.join(genMetDCDir,d,dc), os.path.join(outputDir,d,dc))
            updateSysNumber(os.path.join(outputDir,d,dc))

def updateSysNumber(inputdc) :
    with open(inputdc, 'r') as f :
        lines = f.readlines()

    for iline in range(len(lines)) :
        line = lines[iline]
        if 'kmax' in line :
            nsys = int(line.split()[1])
            print nsys
            newline = line.replace(line.split()[1], str(nsys+1))
            lines[iline] = newline

    with open(inputdc, 'w') as f :
        f.write(''.join(lines))

def makeNewDatacards(inputdc1, inputdc2, outputdc) :
#     print 'producing %s from %s and %s' % (outputdc, inputdc1, inputdc2)
    dcout = ''
    rate1 = 0.0
    rate2 = 0.0
    rateline = ''
    sigsysline = ''

    with open(inputdc1, 'r') as f :
        for line in f :
            if len(line.split()) > 0 and 'mcstat_signal' in line.split()[0] :
                sigsysline = line
                #print sigsysline
            if not 'rate' in line :
                continue
            rateline = line
            rate1 = float(line.split()[1])

    with open(inputdc2, 'r') as f :
        for line in f :
            if not 'rate' in line :
                continue
            rate2 = float(line.split()[1])

    with open(inputdc1, 'r') as f :
        dcout = f.read()

    rateavg = 0.5*(rate1 + rate2)
    newrateline = rateline
    newrateline = newrateline.replace(rateline.split()[1], str(rateavg))
    dcout = dcout.replace(rateline, newrateline)

    metunc = 0.0
    if rateavg > rate2 and rate2 > 0.0 :
        metunc = rateavg/rate2
    elif rateavg > rate1 and rate1 > 0.0 :
        metunc = rateavg/rate1
    metunc = min(2.0, metunc)

    metsysline = sigsysline
    metsysline = metsysline.replace(metsysline.split()[0], 'signal_metunc'+' '*(len(metsysline.split()[0])-len('signal_metunc')))
    metsysline = metsysline.replace('lnN', 'lnU')
    metsysline = metsysline.replace(metsysline.split()[2], '%4.2f' % (metunc))

    #print 'pfMet rate : %4.2f, genMet rate : %4.2f, average rate : %4.2f, uncertainty : %s' % (rate1, rate2, rateavg, metsysline)

    dcout = dcout.replace(sigsysline, metsysline + sigsysline)
    #print dcout

    f = open(outputdc, 'w')
    f.write(dcout)
    f.close()

if __name__=='__main__' : main()
