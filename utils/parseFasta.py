
def readFile(filePath):
    """Reads a file and returns its content.

    Parameters
    ----------
    filePath : str
        The path to the file to be read.

    Returns
    -------
    str
        The content of the file.
    """
    with open(filePath, 'r') as file:
        return file.read()


def parseFasta(filePath):
    """Parses a FASTA file and returns a dictionary of sequences.

    Parameters
    ----------
    filePath : str
        The path to the FASTA file.

    Returns
    -------
    dict
        A dictionary where the keys are sequence headers and the values are the corresponding sequences.
    """
    fileContent = readFile(filePath)
    sequences = {}
    current_header = None
    current_sequence = []

    for line in fileContent.splitlines():
        line = line.strip()
        if line.startswith('>'):
            if current_header:
                sequences[current_header] = ''.join(current_sequence)
            current_header = line[1:]  # Remove '>'
            current_sequence = []
        else:
            current_sequence.append(line)
    else:
        sequences[current_header] = ''.join(current_sequence)

    return sequences



def main():
    filePath = "data/proteomeHumanUniprot.fasta" 
    sequences = parseFasta(filePath)

    print(len(sequences))



if __name__ == '__main__':
    import time
    start_time = time.time()
    main()
    print('--- %s seconds ---' % (time.time() - start_time))