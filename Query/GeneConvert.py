import urllib.parse
import urllib.request
import copy

#query: list of gene names
def convert_genes(query):
    query = [f"{x}_HUMAN" for x in query]
    query = " ".join(query)
    url = 'https://www.uniprot.org/uploadlists/'

    params = {
    'from': 'ID',
    'to': 'ACC',
    'format': 'tab',
    'query': query
    }

    data = urllib.parse.urlencode(params)
    data = data.encode('utf-8')
    req = urllib.request.Request(url, data)
    with urllib.request.urlopen(req) as f:
        response = f.read()
    response = response.decode('utf-8')
    li = response.split("\n")[1:-1]
    
    id_dict = {}
    for x in li:
        uniprot = x.split('\t')[1]
        id_dict[x.split("\t")[0][:-6]] = f"uniprot:{uniprot}" #Key is the gene name w/o _HUMAN, value is uniprot:ID
        
    return id_dict