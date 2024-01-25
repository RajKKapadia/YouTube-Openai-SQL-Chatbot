def get_sql_tool(database_schema_string: str, database_definitions: str) -> list[dict]:
    sql_tool = [
        {
            "type": "function",
            "function": {
                "name": "ask_database",
                "description": "Use this function to answer user questions about Production data. Input should be a fully formed MySQL query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": f"""MySQL query extracting info to answer the user's question. \
MySQL should be written using this database schema: \
{database_schema_string} \
The query should be returned in plain text, not in JSON. \
Don't assume any column names that are not in the database schema, use the \
following data definitions instead: \
{database_definitions}"""
                        }
                    },
                    "required": ["query"],
                },
            }
        }
    ]

    return sql_tool


def get_chat_completion_prompt(query: str, formated_chat_history: list[dict]) -> str:
    chat_completion_prompt = f'''Consider yourselk as a helpful data analyst. A user has asked a \
question: {query}, in the context of the following chat history: {formated_chat_history}, politely reply \
that you don't have the answer for the question.'''

    return chat_completion_prompt


def get_format_sql_response_messages(sql_response: str) -> list[dict]:
    formatted_sql_response_messages = [
        {"role": "system", "content": "Consider yourself as a helpful data analyst. \
You help user get information about the data and answer their question."},
        {"role": "user", "content": f"""Convert the following MySQL data into natural language conversation, \
keep the response short and concise and never mention id of the MySQL data. \
SQL data: {sql_response}"""}
    ]

    return formatted_sql_response_messages


def get_chat_completion_request_system_message() -> dict:
    system_message = {"role": "system", "content": "You are a data analyst. You help user get information \
about the database."}

    return system_message
