import json

from openai_api import chat_completion_request, format_sql_response
from utils import database_schema_string, execute_function_call, database_definitions
from prompts import get_sql_tool, get_chat_completion_prompt

sql_tool = get_sql_tool(database_schema_string, database_definitions)


def format_chat_history(chat_history: list[list]) -> list[list]:
    formated_chat_history = []
    for ch in chat_history:
        formated_chat_history.append({
            'role': 'user',
            'content': ch[0]
        })
        if ch[1] == None:
            pass
        else:
            formated_chat_history.append({
                'role': 'assistant',
                'content': ch[1]
            })

    return formated_chat_history


def handle_chat_completion(chat_history: list[list]) -> list[list]:
    query = chat_history[-1][0]
    print(f'User query -> {query}')
    formated_chat_history = format_chat_history(chat_history)
    chat_response = chat_completion_request(formated_chat_history, sql_tool)
    assistant_message = chat_response["choices"][0]['message']
    if assistant_message['content'] == None:
        '''Call SQL and generate the response.
        '''
        if assistant_message["tool_calls"][0]["function"]["name"] == "ask_database":
            sql_query = json.loads(
                assistant_message["tool_calls"][0]["function"]["arguments"])["query"]
            print(f'SQL query -> {sql_query}')
            sql_response = execute_function_call(sql_query)
            print(f'SQL response -> {sql_response}')
        if sql_response == '':
            chat_completion_prompt = get_chat_completion_prompt(
                query, formated_chat_history)
            response = get_openai_response(chat_completion_prompt)
        else:
            response = format_sql_response(sql_response)
            response = response["choices"][0]['message']['content']
    else:
        response = assistant_message['content']
    print(f'Agent response -> {response}')
    chat_history[-1][1] = response

    return chat_history


def handle_user_query(message: str, chat_history: list[tuple]) -> tuple:
    chat_history += [[message, None]]
    return '', chat_history


def get_openai_response(instruction: str) -> str:
    messages = []
    messages.append({'role': 'user', 'content': instruction})
    response = chat_completion_request(messages)
    response = response['choices'][0]['message']['content']

    return response
