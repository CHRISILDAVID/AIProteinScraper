def generate_search_urls(protein_name):
    protein_queries = [
    {"name": "UniProt", "url": f"https://www.uniprot.org/uniprot/?query={protein_name}"},
    {"name": "PDB", "url": f"https://www.rcsb.org/search?request=%7B%22query%22%3A%7B%22type%22%3A%22group%22%2C%22nodes%22%3A%5B%7B%22type%22%3A%22group%22%2C%22nodes%22%3A%5B%7B%22type%22%3A%22group%22%2C%22nodes%22%3A%5B%7B%22type%22%3A%22terminal%22%2C%22service%22%3A%22full_text%22%2C%22parameters%22%3A%7B%22value%22%3A%22{protein_name}%22%7D%7D%5D%2C%22logical_operator%22%3A%22and%22%7D%5D%2C%22logical_operator%22%3A%22and%22%2C%22label%22%3A%22full_text%22%7D%5D%2C%22logical_operator%22%3A%22and%22%7D%2C%22return_type%22%3A%22entry%22%2C%22request_options%22%3A%7B%22paginate%22%3A%7B%22start%22%3A0%2C%22rows%22%3A25%7D%2C%22results_content_type%22%3A%5B%22experimental%22%5D%2C%22sort%22%3A%5B%7B%22sort_by%22%3A%22score%22%2C%22direction%22%3A%22desc%22%7D%5D%2C%22scoring_strategy%22%3A%22combined%22%7D%2C%22request_info%22%3A%7B%22query_id%22%3A%22ea4bb7297a961131c734f99990065071%22%7D%7D"},
    {"name": "NCBI Protein", "url": f"https://www.ncbi.nlm.nih.gov/protein/?term={protein_name}"},
    {"name": "InterPro", "url": f"https://www.ebi.ac.uk/interpro/search?q={protein_name}"},
    {"name": "KEGG", "url": f"https://www.genome.jp/dbget-bin/www_bfind_sub?mode=bfind&max_hit=100&locale=en&serv=kegg&dbkey=genes&keywords={protein_name}"},
    {"name": "STRING", "url": f"https://string-db.org/newstring_cgi/show_network_section.pl?identifier={protein_name}"}
    ]
    return protein_queries