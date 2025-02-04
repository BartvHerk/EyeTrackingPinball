import csv
from containers import ContGazemap

def import_csv_gazemap(path) -> ContGazemap:
    container = ContGazemap()
    with open(path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        def jump_section(reader, title:str):
            while True:
                if title in next(reader)[0]:
                    return

        # Info
        jump_section(csv_reader, '#INFO')
        csv_info = {}
        while True:
            line = next(csv_reader)
            if line[0] == '#':
                break
            csv_info[line[0].replace('#','')] = line[1]
        for key in container.info.keys(): # Fill only the keys present in ContGazemap
            container.info[key] = csv_info[key]

        # Data
        jump_section(csv_reader, '#DATA')
        headers = next(csv_reader)
        dict_reader = csv.DictReader(csv_file, fieldnames=headers)
        for line in dict_reader:
            if (line['SlideEvent'] != ''): # Skip event rows
                continue
            container_row = {}
            for key in container.data_headers:
                container_row[key] = line[key]
            container.data.append(container_row)
    return container