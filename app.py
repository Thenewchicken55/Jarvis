import streamlit as st
from llm_chains import create_llm_chain


def main():
    st.set_page_config(page_title="Jarvis Chat", page_icon="🤖")
    st.title("Jarvis - AI Assistant")

    if "send_input" not in st.session_state:
        st.session_state.send_input = False
    if "user_question" not in st.session_state:
        st.session_state.user_question = ""
    if "llm_chain" not in st.session_state:
        st.session_state.llm_chain = create_llm_chain()

    chat_container = st.container()

    def set_send_input():
        st.session_state.send_input = True
        st.session_state.user_question = st.session_state.user_input
        st.session_state.user_input = ""

    user_input = st.text_input("Enter your message", key="user_input", on_change=set_send_input)
    send_button = st.button("Send", key="send_button")

    if send_button or st.session_state.send_input:
        if st.session_state.user_question.strip():
            with chat_container:
                st.chat_message("user").write(st.session_state.user_question)
                with st.spinner("Thinking..."):
                    response = st.session_state.llm_chain.run(st.session_state.user_question)
                st.chat_message("ai").write(response)
            st.session_state.send_input = False
            st.session_state.user_question = ""

    with st.sidebar:
        st.subheader("Options")
        if st.button("Clear Conversation"):
            st.session_state.llm_chain.get_memory().clear()
            st.rerun()


if __name__ == "__main__":
    main()
