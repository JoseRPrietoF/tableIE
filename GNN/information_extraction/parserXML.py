"""
python parserXML.py -m coords -i <path a la carpeta con los XML> \
    -t <path al fichero de transcripciones> \
    --output < ruta completa del fichero coords de salida (incluyendo nombre del fichero)> \
    -c HisClima

python parserXML.py -m coords -t ~/transcripciones/hisclima/work_DAEmilio4_retrained/experiment/experiment/beam_decode_10gram_40BEAM_SEARCH_40LATTICE_BEAM_ASF0.5/test_word__all_linesGT3.hyp -i ~/indexing/preproces_lines/data_all/page_lineasGT_bk/ -c HisClima --output hypcoordsGT_HTR
"""
from xml.dom import minidom
import sys
import os
import re
import argparse

OUT_TABLE = "-1"
VALUE_CELL = "0"
COL_HEADER = "1"
ROW_HEADER = "2"

class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y

class Textline():
    def __init__(self, text, x, y, w, h, readingOrder):
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.readingOrder = readingOrder

    def __str__(self):
        return f"{self.x} {self.y} {self.w} {self.h} {self.readingOrder}"

class TableCell():
    def __init__(self, pageID, textLines, tableID, row, col, rowSpan, colSpan, cellType):
        self.pageID = pageID
        self.textLines = textLines
        self.tableID = tableID
        self.row = row
        self.col = col
        self.rowSpan = rowSpan
        self.colSpan = colSpan
        self.cellType = cellType

    def addTextline(self, textline):
        self.textLines.append(textline)
        self.textLines.sort(key=lambda elem: elem.readingOrder)

    def __str__(self):
        s = ""
        for textLine in self.textLines:
            s += (f"{self.pageID} {textLine} {self.tableID} {self.row} {self.col} {self.rowSpan} " +
                f"{self.colSpan} {self.cellType} {textLine.text}\n")
        return s


def writeDicToFile(dict, filePath):
    with open(filePath, 'w') as file_handler:
        for _, list in dict.items():
            for entry in list:
                file_handler.write(f"{entry}")

def getCoords(inputString):
    splitedInput = [elem.split(',') for elem in inputString.split()]
    pointList = [Point(int(elem[0]),int(elem[1])) for elem in splitedInput]
    pointList.sort(key=lambda elem: elem.x)
    w = pointList[-1].x - pointList[0].x
    x = pointList[0].x + (w/2.0)
    pointList.sort(key=lambda elem: elem.y)
    h = pointList[-1].y - pointList[0].y
    y = pointList[0].y + (h/2.0)
    return (x,y,w,h)

def getCellType(tableID, cell, col, row, collection):
    if collection == "HisClima":
        if tableID == 0:
            if(row < 2): return COL_HEADER
            elif (col == 0): return ROW_HEADER
            else: return VALUE_CELL
        else:
            if (col == 0): return ROW_HEADER
            else: return VALUE_CELL
    elif collection == "Passau":
        if(cell.getAttribute('type') == "header"):
            return COL_HEADER
        else:
            return VALUE_CELL

def loadTranscriptions(filePath):
    if filePath is None: 
        return None

    transcriptionsTable = {}

    with open(filePath) as f:
        lines = f.read().splitlines()

    for line in lines:
        line = line.replace("!print","").replace("!manuscript","")
        splittedLine = line.split(" ")
        key = splittedLine[0]
        value = " ".join(splittedLine[1:])
        value = re.sub("\\. "," ",value)
        value = re.sub("\\.$"," ",value)
        value = "".join(value)
        value = value.replace(",","")
        value = value.replace("<decimal>",".")
        transcriptionsTable[key] = value

    return transcriptionsTable

def getText(transcriptionsTable, key, textLine):
    if transcriptionsTable == None:
        text = textLine.getElementsByTagName('Unicode')[0].firstChild.nodeValue
        text = text.replace("!print","").replace("!manuscript","")
    else:
        text = transcriptionsTable[key]
    return text

def getReadingOrder(line):
    beginIndex = line.find("readingOrder {index:") 
    if beginIndex != -1: beginIndex += len("readingOrder {index:")
    endIndex = line.find(";",beginIndex)
    readingOrder = int(line[beginIndex:endIndex])
    return readingOrder

def parseXML(xmlPath, transcriptionsTable, collection):
    res = []
    xmldoc = minidom.parse(xmlPath)
    pageID = xmldoc.getElementsByTagName('Page')[0].getAttribute('imageFilename')
    if pageID[-4:] == ".jpg":
        pageID = pageID[:-4]
    tables = xmldoc.getElementsByTagName('TableRegion')
    textRegions = xmldoc.getElementsByTagName('TextRegion')
    tableCount = 0
    whichOutTable = 0

    for table in tables:
        tableID = table.getAttribute('id')
        for cell in table.getElementsByTagName('TableCell'):
            try:
                row = int(cell.getAttribute('row'))
                col = int(cell.getAttribute('col'))
                colSpan = int(cell.getAttribute('colSpan'))
                rowSpan = int(cell.getAttribute('rowSpan'))
                cellType = getCellType(tableCount, cell, col, row, collection)
                if table in tables[-2:]:
                    whichTable = f"table{tableCount}"
                else:
                    whichTable = f"outTable{whichOutTable}"
                    cellType = OUT_TABLE
                    colSpan = -1
                    rowSpan = -1
                tableCell = TableCell(pageID, [], whichTable, row, col, rowSpan, 
                                        colSpan, cellType)
            except:
                continue
            for textLine in cell.getElementsByTagName('TextLine'):
                coords = textLine.getElementsByTagName('Coords')[0].getAttribute('points')
                x, y, w, h = getCoords(coords)
                textlineID = textLine.getAttribute('id')
                readingOrder = getReadingOrder(textLine.getAttribute('custom'))
                key = f"{pageID}.{tableID}.{textlineID}"
                try:
                    text = getText(transcriptionsTable, key, textLine)
                    textline = Textline(text, x, y, w, h, readingOrder)
                    tableCell.addTextline(textline)
                except:
                    print(f"{pageID}.{tableID}.{textlineID}")
            res.append(tableCell)
        if table in tables[-2:]:
            tableCount += 1
        else:
            whichOutTable += 1

    col = 0

    for textRegion in textRegions:
        regionID = textRegion.getAttribute('id')
        row = 0
        for textLine in textRegion.getElementsByTagName('TextLine'):
            tableCell = TableCell(pageID, [], f"outTable{whichOutTable}", row, col, 
                                    -1, -1, OUT_TABLE)
            row += 1
            coords = textLine.getElementsByTagName('Coords')[0].getAttribute('points')
            x, y, w, h = getCoords(coords)
            textlineID = textLine.getAttribute('id')
            key = f"{pageID}.{regionID}.{textlineID}"
            try:
                text = getText(transcriptionsTable, key, textLine)
                textline = Textline(text, x, y, w, h, 0)
                tableCell.addTextline(textline)
                res.append(tableCell)
            except:
                print(f"{pageID}.{regionID}.{textlineID}")
        whichOutTable += 1
    return res

def XML2hypCoords(xmlPath, transcriptionsTable=None):
    print(xmlPath)
    res = []
    xmldoc = minidom.parse(xmlPath)
    pageID = xmldoc.getElementsByTagName('Page')[0].getAttribute('imageFilename')[:-4]
    tables = xmldoc.getElementsByTagName('TableRegion')
    textRegions = xmldoc.getElementsByTagName('TextRegion')
    tableCount = 0

    for table in tables:
        tableID = table.getAttribute('id')
        for cell in table.getElementsByTagName('TableCell'):
            for textLine in cell.getElementsByTagName('TextLine'):
                coords = textLine.getElementsByTagName('Coords')[0].getAttribute('points')
                textlineID = textLine.getAttribute('id')
                key = f"{pageID}.{tableID}.{textlineID}"
                try:
                    text = getText(transcriptionsTable, key, textLine)
                    entry = f"{pageID}.{textlineID} {text} Coords:( {coords} )\n"
                    res.append(entry)
                except:
                    print(f"{pageID}.{tableID}.{textlineID}")
        tableCount +=1

    for textRegion in textRegions:
        regionID = textRegion.getAttribute('id')
        for textLine in textRegion.getElementsByTagName('TextLine'):
            coords = textLine.getElementsByTagName('Coords')[0].getAttribute('points')
            textlineID = textLine.getAttribute('id')
            key = f"{pageID}.{regionID}.{textlineID}"
            try:
                text = getText(transcriptionsTable, key, textLine)
                entry = f"{pageID}.{textlineID} {text} Coords:( {coords} )\n"
                res.append(entry)
            except:
                print(f"{pageID}.{regionID}.{textlineID}")
    return res

def parseGT(directoryPath, transcriptionsPath, collection, outputFile):
    res = {}
    transcriptionsTable = loadTranscriptions(transcriptionsPath)
    for subdir, dirs, files in os.walk(directoryPath):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(".xml"):
                res[file[:-4]] = parseXML(filepath,transcriptionsTable, collection)
    writeDicToFile(res,outputFile)

def parseHYP(directoryPath, transcriptionsPath, outputFile):
    res = {}
    transcriptionsTable = loadTranscriptions(transcriptionsPath)
    for subdir, dirs, files in os.walk(directoryPath):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(".xml"):
                res[file[:-4]] = XML2hypCoords(filepath,transcriptionsTable)
    writeDicToFile(res,outputFile)

# def getGT(table):
#     res = []

#     for pageID, pageTableCells in table.items():
#         for tableCell1 in pageTableCells:
#             if tableCell1.cellType == COL_HEADER:
#                 for tableCell2 in pageTableCells:
#                     if tableCell2.cellType == ROW_HEADER:
#                         for tableCell3 in pageTableCells:
#                             if tableCell3.cellType == VALUE_CELL:
#                                 if (tableCell2.tableID == tableCell3.tableID and
#                                     tableCell2.row == tableCell3.row):
#                                     if(tableCell1.col):
#                                 # splittedRowKey = rowKey.split()
#                                 # expectedValueKey = f"{splittedRowKey[0]} {splittedRowKey[1]} {splittedColKey[2]}"
#                                 # if  expectedValueKey in valueCellsPage:
#                                 #     valueSpot = valueCellsPage[expectedValueKey]
#                                 #     actualPseudoword = valueSpot[0].pseudoword
#                                 #     if(actualPseudoword == '"!manuscript'):
#                                 #         actualPseudoword += f" [{lastPseudoWord}]"
#                                 #     else:
#                                 #         lastPseudoWord = actualPseudoword
#                                 #     res.append(f"{pageID} {colSpot[0].pseudoword}|{splittedRowKey[0]}_{rowSpot[0].pseudoword} {actualPseudoword}")
                    
#     return res

def parse_args():
    parser = argparse.ArgumentParser(description='This program parses an XML directory')

    parser.add_argument('-m','--mode', choices=['GT', 'coords'], 
                        required=True, help='mode.')

    parser.add_argument('-c','--collection', choices=['HisClima', 'Passau'], 
                        required=True, help='mode.')

    parser.add_argument('-t','--transcriptions', type=str,
                        default=None, help='path to the transcriptions file')
    
    parser.add_argument('-i','--input', type=str,
                        required=True, help='path to the input file')

    parser.add_argument('-o','--output', type=str,
                        required=True, help='path to the output file')
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.mode == 'GT':
        parseGT(args.input, args.transcriptions, args.collection, args.output)
    elif args.mode == 'coords':
        parseHYP(args.input, args.transcriptions, args.output)
