"""Python file to serve as the frontend"""
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.agents import AgentExecutor, LLMSingleActionAgent
from langchain.callbacks import StreamlitCallbackHandler

from document_links import get_info_files
from tool_utils.retrieval_tools import get_retrieval_qa_tools
from output_parsers_utils.custom_output_parsers import EnglishOutputParser, FrenchOutputParser
from prompts_utils.custom_prompts import CustomPromptTemplate, english_agent_template, french_agent_template
from custom_chains_and_agents.custom_chains import get_verification_chain

import logging
import socket
from logging.handlers import SysLogHandler


class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


syslog = SysLogHandler(address=(st.secrets["logging_address"], st.secrets["log_port"]))
syslog.addFilter(ContextFilter())
format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
syslog.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(syslog)
logger.setLevel(logging.INFO)


def load_agent(llm, language="fr"):

    files = get_info_files(language=language)
    tools = get_retrieval_qa_tools(files=files, language=language, create_db=False)
    tool_names = [tool.name for tool in tools]

    if language == "en":
        prompt_template = english_agent_template
        custom_parser = EnglishOutputParser()

    elif language == "fr":
        prompt_template = french_agent_template
        custom_parser = FrenchOutputParser()
    else:
        raise ValueError("Language must be either 'en' or 'fr'")

    custom_prompt = CustomPromptTemplate(
        template=prompt_template,
        tools=tools,
        input_variables=["input", "intermediate_steps"]
    )

    llm_chain = LLMChain(llm=llm, prompt=custom_prompt)

    custom_agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=custom_parser,
        stop=["\nObservation:"],
        allowed_tools=tool_names,
    )

    agent = AgentExecutor.from_agent_and_tools(agent=custom_agent,
                                               tools=tools,
                                               verbose=True,
                                               return_intermediate_steps=True)

    return agent


llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k-0613", streaming=True)
agent = load_agent(llm, 'fr')

verify_chain = get_verification_chain()


def get_source_from_answer(result):

    text = ''
    for source in result['intermediate_steps']:
        for doc in source[1]['source_documents']:
            # print(doc.page_content)
            text += doc.page_content
            text += '\n\n\n'

    return text


# From here down is all the StreamLit UI.
st.set_page_config(page_title="UBS📄 vs BCV📄 💬",
                   page_icon="🏦",
                   layout="wide",
                   initial_sidebar_state="expanded")

st.markdown('<style>.css-w770g5{\
            width: 100%;}\
            .css-b3z5c9{    \
            width: 100%;}\
            .stButton>button{\
            width: 100%;}\
            .stDownloadButton>button{\
            width: 100%;}\
            </style>', unsafe_allow_html=True)


pdf_ubs_url = "https://www.ubs.com/global/fr/legal/country/switzerland/legalnotices/_jcr_content/mainpar/" \
              "toplevelgrid_644694947/col1/linklist_411753453/link.1566204240.file/" \
              "PS9jb250ZW50L2RhbS9hc3NldHMvY2MvZ2xvYmFsL2xlZ2FsL2RvYy9nZW5lcmFsLXRlcm1zL" \
              "WFuZC1jb25kaXRpb25zLWZyLnBkZg==/general-terms-and-conditions-fr.pdf"

pdf_bcv_url = "https://www.bcv.ch/content/dam/bcv/fichiers/conditions/03008FR_2.pdf"
ubs_thumbnail1_url = "static/thumbnail_ubs.png"
bcv_thumbnail2_url = "static/thumbnail_bcv.png"

# Initialize chat history, response, sources and verification
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state['response'] = None
    st.session_state['sources'] = None
    st.session_state['verification'] = None

# Add examples if chat history is empty
if not st.session_state.messages:
    example_questions = [
        "Bienvenue! Je suis un assistant virtuel qui peut vous aider à comparer les documents bancaires de UBS et BCV.",
        "Voici quelques exemples de questions que vous pouvez me poser:\n\nQuelle est la différence entre le secret "
        "bancaire de UBS et celui de BCV?\n\nQuelle est la différence entre la protection des données chez UBS et "
        "celle chez BCV ?\n\nAprès avoir obtenu la réponse finale, vous pouvez voir les extraits des documents qui ont "
        "servi à construire la réponse en cliquant sur 'Voir les sources' en bas à gauche.",
    ]
    for i, question in enumerate(example_questions):
        st.session_state.messages.append({"role": "assistant", "content": f"{question}"})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if user_input := st.chat_input():
    logger.info(f"User input: {user_input}")
    st.session_state['sources'] = None
    st.session_state['verification'] = None
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)
    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent({'input': user_input}, callbacks=[st_callback])
        logger.info(f"Assistant output: {response['output']}")
        st.write(response['output'])
        sources = get_source_from_answer(response)
        st.session_state.messages.append({"role": "assistant", "content": response['output']})
        st.session_state['sources'] = sources

# Display source button if there's a response
sources_ready = False
with st.sidebar:
    st.title('Comparateur de documents')

    cols = st.columns(2)
    cols[0].image(ubs_thumbnail1_url, width=100)
    cols[0].markdown(f'[Consulter PDF]({pdf_ubs_url})', unsafe_allow_html=True)
    cols[1].image(bcv_thumbnail2_url, width=100)
    cols[1].markdown(f'[Consulter PDF]({pdf_bcv_url})', unsafe_allow_html=True)

    readme = "Communiquer avec vos données grâce à l'intelligence artificielle.  \n\nUtilisez cette application pour " \
             "gérer et examiner plusieurs documents à la fois, qu'ils soient courts ou longs. Trouvez les " \
             "informations utiles, comparez les textes, faites des résumés et bien plus. Cette application rend " \
             "l'interaction avec vos documents facile et efficace.  \n\nSi vous souhaitez tester cette application " \
             "avec vos documents, n'hésitez pas à me [joindre](https://www.linkedin.com/in/mmoshek/). Pour ceux qui " \
             "sont intéressés, le code source de l'application est accessible sur mon [Github]" \
             "(https://github.com/Otokpa/UBS_vs_BCV).  " \
             "\n\nLes pionniers de ces nouvelles technologies seront les leaders de demain!"

    st.write(readme)

    # Add empty space
    for _ in range(10):  # Adjust this number as necessary
        st.write("\n")

    st.write('Pour consulter les sources, cliquez sur le bouton suivant.')
    if st.button('Voir les sources'):
        logger.info("User clicked before sources where available")
        if len(st.session_state.messages) and st.session_state.messages[-1][
            'role'] == 'assistant' and 'Ma réponse Finale:' in st.session_state.messages[-1]['content']:
            logger.info("User clicked after sources where available")
            st.write('Juste un moment, je recherche les sources...')

            verification = verify_chain(
                {'answer': st.session_state.messages[-1]['content'], 'text': st.session_state['sources']})
            st.session_state['verification'] = verification
            sources_ready = True

        else:
            st.write('Il n\'y a pas de réponse finale pour vérifier les sources')

    if sources_ready:

        with st.chat_message("assistant"):
            text = st.session_state['verification']['text']
            text = text.replace('\n', '  \n')
            st.write(text)


    st.write('Made by [Maxim Moshek, CFA](https://www.linkedin.com/in/mmoshek/)')








