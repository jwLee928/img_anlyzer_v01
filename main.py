from openai import OpenAI
import streamlit as st
from streamlit_chat import message

# 이미지를 처리하기 위한 파이썬 기본 패키지
import os
import io
import base64
from PIL import Image



### session_state 초기화 ###
if 'OPENAI_API' not in st.session_state:
  st.session_state['OPENAI_API'] = ''
if 'messages' not in st.session_state:
  st.session_state['messages'] = []





### 기능 함수 ###
# 이전 대화를 출력
def print_messages():
  for chat_message in st.session_state['messages']:
    st.chat_message(chat_message['role']).write(chat_message['content'])


# 대화 저장
def add_message(role, message):
  st.session_state['messages'].append(
    {
      'role': role,
      'content': message
    }
  )


# 질문에 답변하기
def askGpt(client, prompt):
  response = client.chat.completions.create(
    model='gpt-4o-mini',
    # messages=[{'role': 'user', 'content': st.session_state['messages']}],
    messages=[{'role': 'user', 'content': prompt}],
    stream=True
  )
  return response


# 이미지 분석 기능
# GPT-4o
def describe(client, prompt, text):
  response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
      {
        'role': 'user',
        'content': [
          {
            'type': 'text',
            'text': prompt
          },
          {
            'type': 'image_url',
            'image_url': {
              'url': text,
            },
          },
        ],
      }
    ],
    stream=True,
    max_tokens=1024,
  )
  return response


# TTS 기능
def TTS(client, response):
  # tts를 활용하여 만든 음성을 파일로 저장
  with client.audio.speech.with_streaming_response.create(
    model='tts-1',
    voice='onyx',
    input=response
  ) as response:
    filename='output.mp3'
    response.stream_to_file(filename)

  # 저장한 음성 파일을 자동 재생
  with open(filename, 'rb') as f:
    data = f.read()
    b64 = base64.b64encode(data).decode()
    # HTML 문법을 사용하여 자동으로 음원을 재생하는 코드 작성
    # 스트림릿에서 HTML을 사용할 수 있는 st.markdown을 활용
    md = f'''
      <audio autoplay='True'>
      <source src='data:audio/mp3;base64,{b64}' type='audio/mp3'>
      </audio>
    '''
    st.markdown(md, unsafe_allow_html=True)

  # 폴더에 남지 않도록 파일 삭제
  os.remove(filename)





### 메인 함수 ###
def main():
  st.set_page_config(page_title='이미지 분석기 v01')

  # 사이드바
  with st.sidebar:
    # 초기화 버튼
    clear_btn = st.button("대화 초기화")

    # OpenAI API 키 입력 받기
    openai_apikey = st.text_input(
      label='API 키 입력',
      placeholder='Enter Your API Key',
      value='',
      type='password'
    )

    # api키 세션 스테이트에 저장
    if openai_apikey:
      st.session_state['OPENAI_API'] = openai_apikey
    st.markdown('---')

  # OpenAI 클라이언트 설정
  if st.session_state['OPENAI_API']:
    client = OpenAI(api_key=st.session_state['OPENAI_API'])
  else:
    st.warning('OpenAI API 키를 입력하세요!')
    return



  # 메인 공간: 채팅 UI
  st.title('OpenAI 기반 이미지 분석 챗봇')


  # 이미지 업로드
  img_file_buffer = st.file_uploader('Upload a PNG or JPG image', type= ['png', 'jpg'])

  if img_file_buffer is not None:
    image = Image.open(img_file_buffer)

    # 업로드한 이미지를 화면에 출력
    st.image(image, caption='Uploaded Image.', use_container_width=True)

    # 이미지 > 바이트 버퍼로 변환
    buffered = io.BytesIO()
    image.save(buffered, format='PNG')

    # 바이트 버퍼 > Base64 인코딩 바이트 문자열로 변환
    img_base64 = base64.b64encode(buffered.getvalue())

    # Base64 인코딩 바이트 문자열 > UTF-8 문자열로 디코딩
    img_base64_str = img_base64.decode('utf-8')

    # GPT-4o에서 입력받을 수 있는 형태로 변환
    image = f'data:image/jpeg;base64,{img_base64_str}'

  # 초기화 버튼 눌리면
  if clear_btn:
    st.session_state['messages'] = []

  # 이전 대화 기록 출력
  print_messages()

  # 사용자 입력
  user_input = st.chat_input('궁금한 내용을 물어보세요!')
  if user_input:
    st.chat_message('user').write(user_input)

    container = st.empty() 
    ai_answer = ""
    # answer = askGpt(client, user_input)
    answer = describe(client, user_input, image)
    for chunk in answer:
      chunk_content = chunk.choices[0].delta.content
      if isinstance(chunk_content, str):
        ai_answer += chunk_content
        container.markdown(ai_answer)

    # 대화 기록을 저장한다.
    add_message('user', user_input)
    add_message('assistant', ai_answer)

    # TTS(client, ai_answer)


  if st.button("TTS 실행"):
    TTS(client, st.session_state['messages'][-1]['content'])

if __name__=='__main__':
  main()