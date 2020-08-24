# app/database/spreadsheet.py

import sys
import json
import csv


class Spreadsheet:
    def __init__(self, filename):
        self.filename = filename        

    def get_row(self):
        with open(self.filename) as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            for line_count, row in enumerate(reader):
                if line_count == 0:
                    #print(f'Column names are {", ".join(row)}')
                    continue
                else:
                    yield row
            
                
if __name__ == '__main__':
    sheet = Spreadsheet('app/database/sales.csv')
    
    for row in sheet.get_row():
        print(f'values = {", ".join(row)}')
