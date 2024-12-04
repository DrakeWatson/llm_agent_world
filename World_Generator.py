"""







"""

import LLM_Controller as llm
import State_Control as st


# TODO create mechanism to force world consistency and information tracking
class WorldState:

    def __init__(self, initial_world_state, initial_information=None):
        if initial_information is None:
            initial_information = []
        self.description = initial_world_state
        self.current_information_list = []
        self._process_state()

    def __str__(self):
        return f"===========\n{self.description} \n {self.current_information_list}"

    def get_next_world_state(self, user_action):
        llm_context = "You will be provided a description of the current world state. You must provide the user" \
                      "a description of the next world state based on their input."
        user_input = f"This is the current world state description: {self.description}\n" \
                     f"Provide a consistent description of the next world state given that {user_action} has just happened."
        llm_query = llm.LlmQuery(llm_context=llm_context, user_input=user_input)
        llm_query.get_response_text()

        self.description = llm_query.response.choices[0].message.content
        self._process_state()

    def _process_state(self):
        llm_context = "You will create a comma separated list of 'information pieces' based on the description provided"
        user_input = f"Turn the follow description into a comma separated list of information.\n" \
                     f"{self.description}\n" \
                     f"As an example, if my description is 'A person walked underneath a tree and picked up an acorn' " \
                     f"then the list created would be: 'person walking', 'underneath a tree', 'picked up an acorn'"

        llm_query = llm.LlmQuery(llm_context=llm_context, user_input=user_input)
        llm_query.get_response_text()

        self.current_information_list = llm_query.response.choices[0].message.content.split(", ")
        temp_list = []
        for info in self.current_information_list:
            temp_list.append(st.Information(info))

        self.current_information_list = temp_list

