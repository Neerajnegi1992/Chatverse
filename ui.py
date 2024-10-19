import streamlit as st
from streamlit_chat import message
import os
import base64
from pathlib import Path
import assistant
from streamlit_pdf_viewer import pdf_viewer
import re
@st.cache_data
#function to display the PDF of a given file 
def displayPDF(file):
    # Opening file from file path
    with open(file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    # Embedding PDF in HTML
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}#zoom=Fit" width="100%" height="600" type="application/pdf"></iframe>'

    # Displaying File
    #st.markdown(pdf_display, unsafe_allow_html=True)
    return pdf_display

def initialize_session_state():
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    if 'generated' not in st.session_state:
        st.session_state['generated'] = ["Hello! Ask me anything"]

    if 'new_chat' not in st.session_state:
        st.session_state['new_chat'] = True

    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hey! 👋"]

def split_pages_(page_no):
    # Split the page numbers into a list
    pages = []
    for part in page_no.split(','):
        part = part.strip().replace('Pages ', '')
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return pages

def split_pages(page_no):
    # Split the page numbers into a list
    pages = []
    for part in page_no.split(','):
        part = part.strip().replace('Pages ', '').replace('Page ', '')
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return pages

def extract_source(source_text):
    #source_text = "**SOURCES:** DMR244663 Rev B CSIP Level 0, pages 19-20"
    print("****&&&&*****inside match",source_text)
    #pattern = r'\*\*SOURCES:\*\* (.*), Pages (\d+(?:-\d+)?(?: , Pages \d+)*)'
    pattern = r'\*\*SOURCES:\*\* (.*), Pages? (\d+(?:-\d+)?(?: , Pages? \d+)*)'
    # Define the pattern to search for
    #pattern = r'SOURCES:.*?(\*\*|\s)?(DMR\d+ Rev [A-Z] CSIP Level \d+), (Pages? \d+(?:-\d+)?(?: , Pages? \d+)*)'
    #pattern = r'SOURCES:.*?(\*\*|\s)?(DMR\d+ Rev [A-Z] CSIP Level \d+), Pages (\d+(?:-\d+)?(?: , Pages \d+)*)'
    #pattern = r'\*?SOURCES?:.*?(\*\*|\s)?(DMR\d+ Rev [A-Z] CSIP Level \d+), (Pages? \d+(?:-\d+)?(?: , Pages? \d+)*)'
    # Search for the pattern in the source text
    match = re.search(pattern, source_text,  re.IGNORECASE | re.MULTILINE)
    
    # If a match is found, return the matched string
    if match:
        filename = match.group(1)
        page_no = match.group(2) 
        pages = split_pages(page_no)
        print("****&&&&*****match filename",filename)
        print("****&&&&*****match page_no",pages)
        return filename,pages
        
    else:
        print("****&&&&*****no match")
        return "No match found",None

def remove_sources_line(source_text):
    # Split the text into lines
    lines = source_text.split('\n')
    
    # Find the index of the line that contains "SOURCES:"
    for i, line in enumerate(lines):
        if "SOURCES:" in line:
            # Return all lines before the "SOURCES:" line
            return '\n'.join(lines[:i])
    
    # If "SOURCES:" is not found, return the original text
    return source_text 
def set_context(query,vector_store):
    if 'product' in st.session_state and 'manual_type' in st.session_state:
    # Filter documents based on selected product and manual type
        filters = {
            "product": st.session_state['product'],
            "manual_type": st.session_state['manual_type']
        }
        relevant_docs = vector_store.similarity_search(query, filters=filters)
    else:
        relevant_docs = vector_store.similarity_search(query)
    return relevant_docs
def conversation_chat(query, chain,vectore_store, history):
    context = set_context(query,vectore_store)
    result = chain({"question": query, "chat_history": history})
    #print("************* result",result["answer"])
    #result["answer"] ="yes"
    history.append((query, result["answer"]))
    page_no = None
    source,page_no = extract_source(result["answer"])
    if source != "No match found":
        print("source created")
        result["answer"] = remove_sources_line(result["answer"])
    return result["answer"],source,page_no

def pdf_scroll():
    with st.sidebar:
        pdf_viewer("DMR244663_zen0.pdf",width=1000, height= 1000,scroll_to_page=11 ) 
def match_filename(filename):
    pattern1 = r'Zenition 70'
    pattern2 = r'Zenition 50/70'
    pattern3 = r'DMR244663'
    # Define the pattern to search for
    #pattern = r'SOURCES:.*?(\*\*|\s)?(DMR\d+ Rev [A-Z] CSIP Level \d+), (Pages? \d+(?:-\d+)?(?: , Pages? \d+)*)'
    #pattern = r'SOURCES:.*?(\*\*|\s)?(DMR\d+ Rev [A-Z] CSIP Level \d+), Pages (\d+(?:-\d+)?(?: , Pages \d+)*)'
    #pattern = r'\*?SOURCES?:.*?(\*\*|\s)?(DMR\d+ Rev [A-Z] CSIP Level \d+), (Pages? \d+(?:-\d+)?(?: , Pages? \d+)*)'
    # Search for the pattern in the source text
    match1 = re.search(pattern1, filename,  re.IGNORECASE | re.MULTILINE)
    match2 = re.search(pattern2, filename,  re.IGNORECASE | re.MULTILINE)
    match3 = re.search(pattern3, filename,  re.IGNORECASE | re.MULTILINE)
    if match1 or match3:
        filename = "DMR244663_zen0.pdf"
        print("match1")
    elif match2:
        filename = "D001026163_Rev_E_Planned_Maintenance_Level_1_Zenition_50_70.pdf"
        print("match2")
    else:
        filename = None
    return filename

def display_pdf_sb():
    with st.sidebar:
        if "page_no" in st.session_state:
            print("Page No.",st.session_state['page_no'])
            print("Filename",st.session_state['filename'])
            filename = match_filename(st.session_state['filename'])
            #pdf_viewer("DMR244663_zen0.pdf",width=1000, height= 1000,scroll_to_page=st.session_state['page_no'][0] )
            if filename is not None:
                print("********pdf display called*******")
                #pdf_viewer(filename, pages_to_render=st.session_state['page_no'])
                pdf_viewer(filename,width=1000, height= 1000,scroll_to_page=st.session_state['page_no'][0] )
    print("displaying sidebar")
    return

def create_link():
    print("*********created link called")
    if "create_link" in st.session_state:
        print("st.session_state['create_link']",st.session_state['create_link'])
        if st.session_state['create_link'] == True:
            #if st.button(str(st.session_state['source_name']), type="primary",on_click=display_pdf_sb):
            if st.button(str(st.session_state['source_name']), type="primary"):
                print("*********created link clicked")
                #display_pdf_sb()
                st.session_state['link_clicked'] = True
                st.rerun(scope='app')

    st.markdown(
        """
        <style>
        button[kind="primary"] {
            background-color: #C0CFFB !important;
            border: none;
            padding: 0 !important;
            color: #3565F6 !important;
            text-decoration: none;
            cursor: pointer;
        }
        button[kind="primary"]:hover {
            text-decoration: underline !important;
            color: #3565F6 !important;
        }
        button[kind="primary"]:focus {
            outline: none !important;
            box-shadow: none !important;
            background-color: lightblue !important;
            color: #3565F6 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    return
def display_chat_history(chain,vectore_store):
    reply_container = st.container()
    container = st.container()
    source = None
    page_no = None
    with container:
        with st.form(key='my_form', clear_on_submit=True):
            user_input = False
            if st.session_state['new_chat']:
                print("^^^^^^^^^^^^^^^^")
                # Step 1: Ask for product and manual type
                product = st.selectbox("Select the product:", ["Zenition 70", "Zenition 50/70"])
                manual_type = st.selectbox("Select the manual type:", ["Repair", "Planned maintenance"])
                submit_button = st.form_submit_button(label='Send')           
                if submit_button:
                    print("here******************")
                    st.session_state['product'] = product
                    st.session_state['manual_type'] = manual_type
                    st.write(f"You selected {product} and {manual_type}.") 
                    st.session_state['new_chat'] = False
                    st.rerun(scope='app')
                    
            else:
                user_input = st.text_input("Question:", placeholder="Ask your question", key='input')
                submit_button = st.form_submit_button(label='Send')
  

        if submit_button:
            if st.session_state['new_chat']:
                print("Submit button clicked for product and manual type selection.")
            else:
                print("Submit button clicked for question submission.")
            if user_input:
                with st.spinner('Generating response...'):
                    st.session_state['question'] ="new"
                    output,source,page_no = conversation_chat(user_input, chain,vectore_store, st.session_state['history'])
                    if page_no is not None:
                        st.session_state['page_no'] = page_no
                        st.session_state['filename'] = source
                        st.session_state['create_link'] = True
                        st.session_state['source_name'] = "&nbsp; Citation: 1. "+ source+" - Page No. "+str(page_no[0])+"&nbsp;&nbsp;"
                        st.session_state['link_clicked'] = False
                    else:
                        st.session_state['create_link'] = False
                        st.session_state['link_clicked'] = True
            
                st.session_state['past'].append(user_input)
                st.session_state['generated'].append(output)

    if st.session_state['generated']:
        with reply_container:
            if st.session_state['new_chat']:
                print("********here 2")
                            
            else:  
                print("**here 3")  
                for i in range(len(st.session_state['generated'])):
                    if len(st.session_state['generated'])>1:
                        with st.chat_message("user"):
                            st.write(st.session_state["past"][i])
                    with st.chat_message("assistant"):
                        st.write(st.session_state["generated"][i])
                        if i == len(st.session_state['generated'])-1:
                            if 'link_clicked' in st.session_state:
                                if st.session_state['link_clicked'] == False:
                                    create_link()
                                else:
                                    create_link()
                                    display_pdf_sb()
                            else:
                                create_link()
        
def main():
    
    # Initialize session state
    initialize_session_state()
    
    # Set page title and layout
    st.set_page_config(page_title="Chat with Your Data", layout="wide")

    # Define colors and icons
    primary_color = "#007bff"
    secondary_color = "#f8f9fa"
    secondary_color ="#f2f2f2"
    base64_string = None
    with open("images/philips_logo.png", "rb") as image_file:
        base64_string = base64.b64encode(image_file.read()).decode()
    # Create header
    #st.markdown(f'<div style="background-color: black; padding: 5px;">'
    #           f'<h1 style="color: white; text-align: center;">Philips Chatbot | MOS</h1></div>', unsafe_allow_html=True)
    # Create header
    st.markdown(f'<div style="background-color: white; padding: 2px;">'
                f'<div style="display: flex; justify-content: space-between;">'
                f'<h1 style="color: blue; text-align: center;">Philips Chatbot | MOS</h1>'
                f'<img src="data:image/png;base64,{base64_string}" alt="Logo" style="height: 100px; margin-right: 20px;">'
                f'</div>'
                f'</div>', unsafe_allow_html=True)
    # Display the logo image
    #st.image("images/philips_logo.png", width=100)
    # Create main container
    st.markdown("<hr>", unsafe_allow_html=True)
    st.header("Frequently asked questions")
    

    # Create question cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div style="border: 1px solid {secondary_color}; padding: 2px; border-radius: 2px; background-color: {secondary_color};">'
                    f'<p style="font-weight: bold;">X-Ray tank replacement?</p>'
                    f'</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div style="border: 1px solid {secondary_color}; padding: 2px; border-radius: 2px; background-color: {secondary_color};">'
                    f'<p style="font-weight: bold;">How to replace the collimator?</p>'
                    f'</div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div style="border: 1px solid {secondary_color}; padding: 2px; border-radius: 2px; background-color: {secondary_color};">'
                    f'<p style="font-weight: bold;">Laser Alignment</p>'
                    f'</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    #pdf_view = displayPDF("gagechek_2000_demo.pdf")
    
    

            #pdf_viewer("DMR244663_zen0.pdf",width=1000, height= 1000,scroll_to_page=st.session_state['page_no'][0])
        #pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_view}#zoom=Fit" width="100%" height="600" type="application/pdf"></iframe>'
    #    if st.checkbox("Show PDF"):
            #pdf_viewer("DMR244663_zen0.pdf")
    #        print("***here")
            #pdf_viewer("DMR244663_zen0.pdf",width=1000, height= 1000,scroll_to_page=11 )
            #st.markdown(pdf_view, unsafe_allow_html=True)
    #print("**********before display chat histoy")
    if 'product' in st.session_state and 'manual_type' in st.session_state :
        chain,vectore_store = assistant.get_chain(st.session_state['product'],st.session_state['manual_type'])
    else:
        chain,vectore_store = assistant.get_chain(None,None)
    display_chat_history(chain,vectore_store)     
    #print("**********after display chat histoy")

        

  
 
    

if __name__ == "__main__":
    main()