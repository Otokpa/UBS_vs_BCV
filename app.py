"""Python file to serve as the frontend"""
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.agents import AgentExecutor, LLMSingleActionAgent
from langchain.callbacks import StreamlitCallbackHandler
from langchain.memory import ConversationBufferMemory

from document_links import get_info_files
from tool_utils.retrieval_tools import get_retrieval_qa_tools
from output_parsers_utils.custom_output_parsers import EnglishOutputParser, FrenchOutputParser
from prompts_utils.custom_prompts import CustomPromptTemplate, english_agent_template, french_agent_template
from custom_chains_and_agents.custom_chains import get_verification_chain

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

    agent = AgentExecutor.from_agent_and_tools(agent=custom_agent, tools=tools, verbose=True, return_intermediate_steps=True)

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


# llm_chain.predict(answer=result['output'], text=text)


# From here down is all the StreamLit UI.
st.set_page_config(page_title="UBS vs BCV ", page_icon=":robot:")
st.header("Comparateur de documents bancaires")


st.title("UBS vs BCV")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").write(user_input)
    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        response = agent({'input': user_input}, callbacks=[st_callback])
        sources = get_source_from_answer(response)
        verification = verify_chain({'answer': response['output'], 'text': sources})
        st.write(response['output'])
        st.write(verification['text'])

    st.session_state.messages.append({"role": "assistant", "content": response})
