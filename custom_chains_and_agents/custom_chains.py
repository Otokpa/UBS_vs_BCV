from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate


import streamlit as st

def get_verification_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k-0613", streaming=True)

    template = """En tant que modèle de langage doté d'une capacité d'expert pour analyser et retracer l'information, votre tâche consiste à évaluer la réponse donnée et à identifier si ses faits sont tirés du texte fourni. Voici la réponse à examiner:
    
        {answer}
    
        Voici le texte original à partir duquel toutes les informations dans la réponse auraient dû être extraites:
    
        {text}
    
        Pour chaque fait présent dans la réponse, veuillez les identifier et les lister avec leurs sources correspondantes du texte. Veuillez suivre ce format :
    
        Fait: Énoncé factuel de la réponse
        La Section: section du texte original
        La Source: extrait du texte original
        """

    prompt = PromptTemplate(template=template, input_variables=["answer", "text"])
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    return llm_chain








