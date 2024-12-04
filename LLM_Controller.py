"""







"""
import openai
import json

_LLM_MODEL = "gpt-3.5-turbo"
_RETRIES = 3
# TODO Make this a file read instead of harcdcoded TODO TODO
openai.api_key = ""

_GET_RESPONSE_CONTENT = ""


def _get_llm_response(messages, tools=None, tool_choice=None):
    """
    Basic wrapper function for prompting and handling errors from LLM.

    :messages: A formatted 'messages' input for sending to LLM. See: https://platform.openai.com/docs/api-reference/messages
    :return: The LLM's response
    """
    retry = _RETRIES
    response = {}
    while retry:
        retry -= 1
        try:
            response = openai.ChatCompletion.create(model=_LLM_MODEL, messages=messages, tools=tools, tool_choice=tool_choice)
        # From https://help.openai.com/en/articles/6897213-openai-library-error-types-guidance
        except openai.error.Timeout as e:
            # Retry if we still can
            print(f"OpenAI API request timed out: {e}")
            continue

        except openai.error.APIError as e:
            # Retry if we still can
            print(f"OpenAI API returned an API Error: {e}")
            continue

        except openai.error.APIConnectionError as e:
            # Raise error related to internet connection failure
            raise RuntimeError(f"OpenAI API request failed to connect: {e}\n Messages: {messages}")

        except openai.error.InvalidRequestError as e:
            # Raise error related to incorrect messages
            raise RuntimeError(f"InvalidRequestError: {e}\n Messages: {messages}")

        except openai.error.AuthenticationError as e:
            # Raise error related to Authentication problem
            raise RuntimeError(f"AuthenticationError: {e}\n Messages: {messages}")

        except openai.error.PermissionError as e:
            # Raise error related to permission problem
            raise RuntimeError(f"PermissionError: {e}\n Messages: {messages}")

        except openai.error.RateLimitError as e:
            # Retry if we still can
            print(f"OpenAI RateLimitError hit: {e}\n Messages: {messages}")
            continue

        except Exception as e:
            # Raise error for unexpected case
            raise RuntimeError(f"Unexpected Error hit during LLM query: {e}\n Messages: {messages}")

    # TODO add check for tool_choice and if function call is forced ensure the response fits the required format
    return response


class LlmQuery:
    """
    Class containing data for/from LLM responses
    """

    def __init__(self, llm_role="system", user_role="user", llm_context="", user_input="", function_dict=None):
        if function_dict is None:
            function_dict = {}
        self.llm_role = llm_role
        self.user_role = user_role
        self.llm_context = llm_context
        self.user_input = user_input
        self.function_dict = function_dict
        self.response = ""

    def get_response_text(self):
        messages = [{"role": self.llm_role, "content": self.llm_context}, {"role": self.user_role, "content": self.user_input}]
        self.response = _get_llm_response(messages)
        return self.response

    def get_response_function(self):
        messages = [{"role": self.llm_role, "content": _GET_RESPONSE_CONTENT},
                    {"role": self.user_role, "content": f"{self.user_input} Dictionary of functions: {self.function_dict}"}]
        llm_function_helper_dict = {
            'type': 'function',
            'function': {
                'name': '_llm_function_helper',
                'description': 'You have to call this function. There is no other option.',
                "parameters": {
                    "type": "object",
                    "properties": {
                        'function_choice': {
                            'type': 'string',
                            'description': 'Name of the function to call'
                        },
                        'parameter_dict': {
                            'type': 'object',
                            'description': 'An object where the keys are the names of the parameters used by the '
                                           'function selected in function_choice and the values are the value for that '
                                           'parameter name.'
                        }

                    },
                    "required": ["function_choice", "parameter_dict"]

                }

            }
        }

        self.response = _get_llm_response(messages, tools=[llm_function_helper_dict])

        function_name = self.response.choices[0].message.tool_calls[0].function.name
        arguments = self.response.choices[0].message.tool_calls[0].function.arguments

        function_response = _llm_function_helper(function_name, arguments)

        return function_response


def _llm_function_helper(function_name, arguments):
    """
    Used as the function the LLM is forced to select when responding as a way of calling other functions

    :param function_name: The name of the function to be called
    :param arguments: A dictionary of the parameters to be used in the function
    :return: Returns the result of whatever function is called
    """
    arguments = json.loads(arguments)
    return_val = globals()[function_name](**arguments)  # Call the function

    return return_val