# Description: This file contains the links to the documents that will be used for the project

def get_info_files(language='en'):
    if language == "en":
        bcv_path = 'bank_docs/bcv_general-terms-and-conditions-en.txt'
        ubs_path = 'bank_docs/ubs_general-terms-and-conditions-en.txt'
        bcv_name = "bcv_general-terms-and-conditions-en"
        ubs_name = "ubs_general-terms-and-conditions-en"
        input_format = "The specific piece of information you want from the document"

    elif language == "fr":
        bcv_path = 'bank_docs/bcv_general-terms-and-conditions-fr.txt'
        ubs_path = 'bank_docs/ubs_general-terms-and-conditions-fr.txt'
        bcv_name = "bcv_outil_d_extraction_condition_general"
        ubs_name = "ubs_outil_d_extraction_condition_general"
        input_format = "La pièce spécifique d'information que vous souhaitez obtenir du document"

    else:
        raise ValueError("Language must be either 'en' or 'fr'")

    store_directory = 'bank_docs/'

    files = [
        {
            "name": bcv_name,
            "input_format": input_format,
            "path": bcv_path,
            "store_directory": store_directory + "bcv/" + language + "/",
            "chunk_size": 1500,
            "chunk_overlap": 0,
            "return_source_documents": False,
            "return_direct": False,
        },
        {
            "name": ubs_name,
            "input_format": input_format,
            "path": ubs_path,
            "store_directory": store_directory + "ubs/" + language + "/",
            "chunk_size": 1500,
            "chunk_overlap": 0,
            "return_source_documents": False,
            "return_direct": False,
        },
    ]

    return files
