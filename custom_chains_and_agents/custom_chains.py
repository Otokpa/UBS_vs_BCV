from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate


def get_verification_chain():
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k-0613", streaming=True)

    template = """En tant que modèle de langage doté d'une capacité d'expert pour analyser et retracer l'information, votre tâche consiste à évaluer la réponse donnée et à identifier si ses faits sont tirés du texte fourni. Voici la réponse à examiner :

        {answer}

        Voici le texte original à partir duquel toutes les informations dans la réponse auraient dû être extraites :

        {text}

        Pour effectuer cette tâche, suivez ces étapes:

        1. Extraire tous les faits présents dans la réponse. Notez qu'une seule phrase peut contenir plusieurs faits.

        2. Pour chaque fait identifié, recherchez sa source correspondante dans le texte original.

        3. Lister les faits et leurs sources en suivant ce format :

        FAIT: Énoncé factuel de la réponse

        LA SECTION: section du texte original où la source du fait est située.

        LA SOURCE: *extrait du texte original qui contient le fait*

        Par conséquent, votre résultat final devrait être une liste de faits avec les sections correspondantes et leurs sources dans le texte original."""

    prompt = PromptTemplate(template=template, input_variables=["answer", "text"])
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    return llm_chain








