import urllib.request
from tqdm import tqdm
import os
import json


def downloadSignalSequenceByProteome(proteomeIds=["UP000005640"],redownload=False):
    """
    Download UniProt "signal peptide" feature data for one or more proteomes and save each
    proteome's JSON response to a local file.
    proteomeIds : list of str, optional
        List of UniProt proteome accessions to fetch (default ["UP000005640"] - Home Sapiens).
        The function constructs a single UniProt query containing all IDs (formatted as
        '(proteome:ID1 OR proteome:ID2 ...)') and sends one HTTP request for that combined
        query. For each proteomeId in the provided list a separate output file is created
        (data/signalProteomes/{proteomeId}.json).
    redownload : bool, optional
        If False (default) the function will skip downloading for any proteomeId that
        already has a corresponding file at data/signalProteomes/{proteomeId}.json.
        If True, the function forces re-download and overwrites existing files.
    Returns
    -------
    None
        The function writes JSON text files to disk and prints progress messages. It does
        not return any value.
    Side effects
    ------------
    - Performs an HTTP GET request to the UniProt REST API to retrieve the fields
      accession, id, and ft_signal in JSON format.
    - Writes the raw JSON response (UTF-8 decoded) to data/signalProteomes/{proteomeId}.json
      for each requested proteomeId.
    - Displays console output and a tqdm progress bar while downloading.
    - May create or overwrite files under the data/signalProteomes/ directory.
    Notes
    -----
    - The function relies on urllib.request to fetch data, tqdm for progress display, and os
      for filesystem checks; these should be imported in the module where the function is used.
    - If the HTTP response includes a Content-Length header, it is used to size the progress bar.
    - The URL is constructed by joining the provided proteomeIds into a single query string;
      this means one HTTP response is fetched per invocation and then saved to the per-proteome files.
    - The saved files contain the JSON text returned by UniProt; no parsing of the JSON is performed
      before writing.
    Exceptions
    Network and I/O errors (e.g., urllib.error.URLError, urllib.error.HTTPError, OSError)
    may be raised when fetching or writing data.
    Examples
    --------
    >>> getSignal(["UP000005640"])
    # Downloads data and writes to data/signalProteomes/UP000005640.json (or skips if already present)
    """
    basePath = "data/signalProteomes/"
    if not os.path.exists(basePath):
        os.makedirs(basePath)
    for proteomeId in proteomeIds:
        # skip if already downloaded
        if os.path.exists(f"{basePath}{proteomeId}.json") and not redownload:
            print(f"Signal peptides for proteome {proteomeId} already downloaded. Skipping... Set redownload=True to force re-download.")
            continue
        print(f"Fetching signal peptides for proteome {proteomeId}...")
        baseUrl = "https://rest.uniprot.org/uniprotkb/stream?compressed=false&format=json&query=%s&fields=accession,id,ft_signal"
        proteomes = f'(proteome:{" OR proteome:" .join(proteomeIds)})'
        url = baseUrl % proteomes
        url = url.replace(" ", "%20")
        # progress bar code
        with urllib.request.urlopen(url) as response:
            total = response.getheader('Content-Length')
            total = int(total) if total else None
            chunks = []
            with tqdm(total=total, unit='B', unit_scale=True, desc=f'Downloading {proteomeId}') as pbar:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    pbar.update(len(chunk))
                    
            content = b''.join(chunks).decode('utf-8')
            
        # save to file
        with open(f"{basePath}{proteomeId}.json", 'w') as outFile:
            outFile.write(content)
        

def parseSignalPeptides(proteomeId):
    """
    Parse the signal peptide data for a given proteomeId from the corresponding JSON file
    saved by getSignal(). Extracts and returns a dictionary mapping protein accessions to
    their signal peptide start and end positions.
    proteomeId : str
        The UniProt proteome accession corresponding to the JSON file to parse
        (e.g., "UP000005640").
    Returns
    -------
    dict
        A dictionary where keys are either protein accessions (str) or protein names (str) and values are tuples of
        (start, end) positions (int) of the signal peptide. If a protein has no signal
        peptide, it will not be included in the dictionary.
    """
    basePath = "data/signalProteomes/"
    signalPeptides = {"accession":{},"protein_name":{}}
    with open(f"{basePath}{proteomeId}.json", 'r') as inFile:
        data = json.load(inFile)
        for entry in data['results']:
            accession = entry['primaryAccession']
            protein_name = entry['uniProtkbId']
            features = entry.get('features', [])
            for feature in features:
                if feature['type'] == 'Signal':
                    start = feature['location']['start']['value']
                    end = feature['location']['end']['value']
                    signalPeptides["accession"][accession] = (start, end)
                    signalPeptides["protein_name"][protein_name] = (start, end)
    return signalPeptides


def getSignalProteome(proteomeId="UP000005640"):
    # ensure that our proteome is downloaded
    downloadSignalSequenceByProteome(proteomeIds=[proteomeId],redownload=False)
    signalProteins = parseSignalPeptides(proteomeId=proteomeId)
    return signalProteins


if __name__ == '__main__':
    import time
    start_time = time.time()
    downloadSignalSequenceByProteome(["UP000005640","UP000000589"], redownload=False)
    print(parseSignalPeptides("UP000005640"))
    print('--- %s seconds ---' % (time.time() - start_time))

