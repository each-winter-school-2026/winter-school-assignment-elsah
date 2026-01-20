abundance_dict = {}

abundanceFile = "data/proteomes/Arabidopsis/arabidopsis_leaf_proteins_detected_by_MS.txt" # Ensure concentration is on g/ml
entryNameMode = True

baseProteome = "data/proteomes/Arabidopsis/proteomeArabidopsis.fasta"
abundanceProteome = "data/proteomes/Arabidopsis/proteomeArabidopsis_with_abundance.fasta"

with open(abundanceFile, 'r') as file:
    file.readline()  # Skip header line
    for line in file:
        parts = line.strip().split('\t')
        if len(parts) == 2:
            header, abundance = parts
            abundance_dict[header] = float(abundance)



    with open(baseProteome, 'r') as fastaFile, open(abundanceProteome, 'w') as outputFile:
        for line in fastaFile:
            if line.startswith('>'):
                abundance = None
                header = line.split("|")[2]
                
                if entryNameMode:
                    proteinIdentifier = header.split(" ")[0]
                else:
                    if "GN=" in header:
                        proteinIdentifier = header.split("GN=")[1].split(" ")[0]
                    
                abundance = abundance_dict.get(proteinIdentifier, None)
                if abundance is not None:
                    outputFile.write(f"{line.strip()} AB={abundance}\n")
                else:
                    outputFile.write(f"{line.strip()} AB={0.0}\n")
            else:
                outputFile.write(line)