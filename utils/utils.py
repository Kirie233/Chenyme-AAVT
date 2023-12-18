import tempfile
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)


def generate_srt_from_result(result):  # 格式化为SRT字幕的形式
    segments = result['segments']
    srt_content = ''
    segment_id = 1
    for segment in segments:
        start_time = int(segment['start'] * 1000)
        end_time = int(segment['end'] * 1000)
        text = segment['text']

        srt_content += f"{segment_id}\n"
        srt_content += f"{milliseconds_to_srt_time_format(start_time)} --> {milliseconds_to_srt_time_format(end_time)}\n"
        srt_content += f"{text}\n\n"
        segment_id += 1

    return srt_content


def milliseconds_to_srt_time_format(milliseconds):  # 将毫秒表示的时间转换为SRT字幕的时间格式
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def tmp_filepath(uploaded_file):  # 虚拟化文件路径
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
    return tmp_file.name


def openai_translate(key, base, result):
    llm = ChatOpenAI(openai_api_key=key, openai_api_base=base)
    # Prompt
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(
                "You are a senior translator proficient in Chinese and English. Your task is to translate whatever the user says. You only need to answer the translation result and do not use punctuation marks other than question marks. Please strictly implement it!"
            ),
            # The `variable_name` here is what must align with memory
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}"),
        ]
    )
    # 设置记忆参数
    memory = ConversationBufferWindowMemory(memory_key="chat_history", return_messages=True, k=5)
    conversation = LLMChain(llm=llm, prompt=prompt, verbose=False, memory=memory)
    segments = result['segments']
    segment_id = 0
    for segment in segments:
        text = segment['text']
        response = conversation({"question": text})
        result['segments'][segment_id]['text'] = response['text']
        segment_id += 1
    return result
