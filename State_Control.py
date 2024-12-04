"""

TODO
- Add logging
- Add model training for specific functions for greater accuracy and lower latency
- Reduce prompt / token size by A LOT
- Reformat information / context / memory into a data struct that allows for easy refactoring, contextualization, and
compression.
- Add multithreading to all LLM prompts / Agent internal functions


Current memories: "I am walking." "I have seen a lot of paint drops." "I am afraid of confined spaces"
"You walk into a room and see a colorful pattern painted on the walls."

Information objects that should be created:

"""

from LLM_Controller import LlmQuery
from World_Generator import WorldState


class Information:
    """
    Information is constructed of context (list of links to other information).
    Information can be created, processed, and manipulated by both an agent and the world.
    The world can only create information that has no context.
    An agent can only create information that has context.
    """

    def __init__(self, information, context_of_information=None):
        if context_of_information is None:
            context_of_information = []
        self.value = information  # A string of any information
        self.context_of_information = context_of_information  # A list of keys for other information that provides context

    def __str__(self):
        return self.value


def information_from_context(context_list):
    """
    Takes a list of any type of context object and returns just the information objects
    :param context_list: Any kind of context object
    :return:
    """
    information_list = []
    for context in context_list:  # Extract all information objects from the context
        if context.what not in information_list:
            information_list.append(context.what)  # Returns an information object
        if context.get_information() not in information_list:
            information_list += context.get_information()  # Returns a list of information objects

    return information_list


def contextualize_information(information, context_information, explanation, explanation_details):
    """
    Takes in an information object, a context list, and a user phrase and then produces
    a string describing the information with the use of LLM
    :param information: Information object
    :param context_information: List of information objects that correspond to the information object
    :param explanation: A string providing the sentence format for the explanation
    :param explanation_details: An extra string used to supplement the explanation
    :return:
    """
    short_context_list = []
    for info in context_information:
        if info.value not in [short_context_list]:
            short_context_list.append(info.value)

    llm_context = "Create a single sentence by combining some context to explain a piece of information. Response must " \
                  "be in the first person."
    if len(context_information) < 1:  # If there is no context to a piece of information, it is its own context.
        return information.value
    else:
        user_input = f"The information is: {information.value}.\nThe context is: {short_context_list}.\n" \
                     f"Create a sentence in which the context describes {explanation} {explanation_details}." \
                     f" The phrase '{explanation}' must be used in the sentence."
    #  print(user_input)
    llm = LlmQuery(llm_context=llm_context, user_input=user_input)
    llm.get_response_text()
    #  print(f"Response: {llm.response.choices[0].message.content}\n")
    return llm.response.choices[0].message.content


def assign_context(information_list, memory_object):
    """
    Using a memory object assign context to the information in the list of information objects

    :param information_list: List of information objects
    :param memory_object: AgentMemory object
    :return: updated information list and the time left after operation is performed
    """
    # TODO launch multiple threads ? Current approach is serial, parallel implementation is possible
    for list_index, stimulus in enumerate(information_list):
        #  print(f"Getting context for {stimulus.value}")
        stimulus.context_of_information, context_time_left = memory_object.get_context(stimulus)
        information_list[list_index] = stimulus

    return information_list


class AgentState:
    """
    Holds the current state of an agent
    """

    def __init__(self, understood_context=None, spatial_context=None, emotional_context=None,
                 internal_context=None, social_context=None, temporal_context=None):
        # Lists of our current context
        self.understood_context_list = [understood_context]
        self.spatial_context_list = [spatial_context]
        self.emotional_context_list = [emotional_context]
        self.internal_context_list = [internal_context]
        self.social_context_list = [social_context]
        self.temporal_context_list = [temporal_context]

    def update_context(self, stimulus_list, memory_object):

        # Contextualize the new information in the stimulus list as much as we can
        contextualized_stimulus_list = assign_context(stimulus_list, memory_object)

        # Update and compress our current context with the new information
        return self._refactor_context(contextualized_stimulus_list, memory_object)

    def _refactor_context(self, stimulus_list, memory_object):

        # Add the contextualized information to our AgentState
        new_temp = TemporalContext(Information("Is currently happening", self.temporal_context_list))
        new_temp.experienced_information = stimulus_list
        self.temporal_context_list.append(new_temp)

        # Compress our current context
        # TODO Launch threads ?

        return 0


class AgentMemory:
    """
    An agent's memories
    """

    def __init__(self):
        self.memories = []  # A list of temporal contexts

    def store(self, agent_state, response):
        # TODO Process agent state as to only store context and information
        # TODO include response in memory storage
        self.memories += agent_state.temporal_context_list

    def refactor(self):
        # TODO refactor
        # TODO search algorithm through memories and then decide what to be merged
        previous_memory = None
        for memory in self.memories:  # For now just merge all temporal contexts
            memory.merge_temporal_context(previous_memory)

    def get_context(self, information):
        """
        Returns a list of as many relevant context objects we can find in the time allowed for the information object
        :param information: Information we are retrieving context for
        :return: A list of context objects
        """
        context_list = []
        # print(f"Assigning context for {information}")
        # Ask LLM what type of information this is
        llm_context = "Select one of the following categories of information: Understood, Spatial, Internal, " \
                      "Emotional, or Social"
        user_input = f"Understood - Why something exists.\n" \
                     f"Spatial - Where something exists.\n" \
                     f"Internal - What I think about something.\n" \
                     f"Emotional - What I feel about something.\n" \
                     f"Social - Who is existing\n" \
                     f"Based on the provided definitions above, respond with a single word that is the category that" \
                     f"{information} best fits into"

        llm = LlmQuery(llm_context=llm_context, user_input=user_input)
        llm.get_response_text()

        category = llm.response.choices[0].message.content
        for memory in self.memories:
            for context in get_relevant_context(information, memory.experienced_information, category):
                if context not in context_list:
                    context_list.append(context)

        return context_list


def get_relevant_context(information, information_list, category):
    """
    Takes an information object and searches an information list for relevant context
    :param information: Information object
    :param information_list: List of information objects that may hold context relevant to the information
    :param category: The category of context
    :return: List of context objects that are relevant to the information
    """
    context_list = []
    llm_context = "Respond 'Yes' or 'No' to the user's question"
    # print(information_list)
    for info_obj in information_list:
        # print(info_obj)
        context_str = ""
        for context_obj in info_obj.context_of_information:
            context_str += f"{context_obj.what}, "

        user_input = f"Respond yes or no, is {information.value} relevant to {info_obj.value} within the context of " \
                     f"{context_str}"
        llm = LlmQuery(llm_context=llm_context, user_input=user_input)
        llm.get_response_text()
        first_response = llm.response.choices[0].message.content.lower()

        user_input = f"Respond yes or no, generally would {information.value} provide {category} context?"
        llm = LlmQuery(llm_context=llm_context, user_input=user_input)
        llm.get_response_text()

        if 'yes' in llm.response.choices[0].message.content.lower() and 'yes' in first_response.lower():
            # print(f"Adding {len(info_obj.context_of_information)} context objects to {information}")
            context_list += info_obj.context_of_information

    return context_list


class Agent:
    """
    An agent that can independently interact with the world
    """

    def __init__(self):
        self.previous_agent_state = AgentState()  # The AgentState just before our current one
        self.current_agent_state = AgentState()  # The agent's current informational context
        self.memories = AgentMemory()  # The agent's memories
        self.stimulus_list = []  # The current stimulus provided by the world
        self.stimulus_description = ""  # A description of the stimulus list

        context_dict, info_list = get_fundamentals()

        temporal_context = TemporalContext(info_list[0])  # info_list[0] selects the temporal information object

        self.previous_agent_state = AgentState(temporal_context=temporal_context)
        # print(f"Initialize Agent1: {self.previous_agent_state.temporal_context_list}")
        self.current_agent_state = self.previous_agent_state  # All we know and have ever known is that we exist
        # print(f"Initialize Agent2: {self.current_agent_state.temporal_context_list}")

    def process_stimulus(self, stimulus_description, stimulus_list):  # Process an input from the world

        self.stimulus_list = stimulus_list
        self.stimulus_description = stimulus_description  # TODO Propagate stimulus_description into update_context

        # Process the stimulus and change our current AgentState
        response = self.get_response()

        # Record the response we chose
        self.memories.store(self.current_agent_state, response)

        # Refactor our memory if we have any time left to process (will usually happen during downtime)
        # self.memories.refactor()

        # Update our previous agent state to create a perfect memory of the 'moment' just before this one
        self.previous_agent_state = self.current_agent_state

        return response

    def get_response(self):

        # Process information to update the AgentState based on our current AgentState and the stimulus
        self.current_agent_state.update_context(self.stimulus_list, self.memories)

        # Now that we have the updated context determine how the agent could respond
        response_list = self._generate_response_list()

        # Choose a response based on our AgentState
        response = self._choose_response(response_list)

        return response

    def _generate_response_list(self):
        """
        Using an LLM generate a list of possible responses
        :return:
        """
        response_list = []
        current_context_string = ""
        # print(self.current_agent_state.temporal_context_list)
        for temporal_context in self.current_agent_state.temporal_context_list:
            current_context_string += f"{temporal_context.get_contextualized_information()}.\n"

        # print(f"Generating response list... Current context string: \n    {current_context_string}\n")
        # TODO this needs to use the function selector LLM since we want to be able to correctly parse actions
        llm_context = "Create a comma separated list of possible actions to take by pretending to be someone."
        user_input = f"Given the following information, create a comma separated list of possible responses if you were" \
                     f" the person described.\n" \
                     f"Description of what has just happened:\n{self.stimulus_description}\n" \
                     f"The person's current context is:\n{current_context_string}\n" \
                     f"As an example, if my information is 'I walked underneath a tree and picked up an acorn' " \
                     f"then the possible responses might be: 'throw acorn', 'sigh at acorn', 'stare at acorn', " \
                     f"'do nothing'"

        llm_query = LlmQuery(llm_context=llm_context, user_input=user_input)
        llm_query.get_response_text()

        self.response_list = llm_query.response.choices[0].message.content.split(", ")

        return response_list

    def _choose_response(self, response_list):
        """
        Using an LLM choose one of the possible responses to use based on the context
        :param response_list: A list of possible responses to return
        :return:
        """
        current_context_string = ""
        for temporal_context in self.current_agent_state.temporal_context_list:
            current_context_string += f"{temporal_context.get_contextualized_information()}.\n"

        llm_context = "Pretend you are a person who's internal context will be described by the user. Based on that " \
                      "context you will choose one of the possible responses provided by the user."
        user_input = f"The following has just happened:\n{self.stimulus_description}\n" \
                     f"Pretend you are the person with the following context:\n{current_context_string}\n" \
                     f"If you were that person given what has just happened, based on the following list of possible" \
                     f"responses which would you do? Possible responses:\n{response_list}"

        llm_query = LlmQuery(llm_context=llm_context, user_input=user_input)
        llm_query.get_response_text()

        response = llm_query.response.choices[0].message.content

        return response


def compress_context(list_of_context):
    """
    Takes a list of context objects of the same type and compresses them into a single context object of that type
    :return: Returns an information object whose value is a string describing the compressed context
    """

    context_string = ""
    for context in list_of_context:
        context_string += f"{context.get_contextualized_information()}. "
    llm_context = "Combine several pieces of information into a single sentence."
    user_input = f"Given the following information: \n{context_string}\n" \
                 f"Return a single sentence that includes all of it."

    llm_query = LlmQuery(llm_context=llm_context, user_input=user_input)
    llm_query.get_response_text()

    return Information(llm_query.response.choices[0].message.content, list_of_context), 0


def main():
    """
    while(running):

        world_gen.apply_response(agent.process_stimulus(world_gen.create_next_stimulus()))

    :return:
    """

    cheese_agent = Agent()

    world = WorldState("You exist.")
    print(world)
    print("")

    response = cheese_agent.process_stimulus(world.description, world.current_information_list)
    print(f"Agent response:\n {response}\n")
    world.get_next_world_state(response)
    print(world)
    print("")

    response = cheese_agent.process_stimulus(world.description, world.current_information_list)
    print(f"Agent response:\n {response}\n")
    world.get_next_world_state(response)
    print(world)
    print("")

    response = cheese_agent.process_stimulus(world.description, world.current_information_list)
    print(f"Agent response:\n {response}\n")
    world.get_next_world_state(response)
    print(world)
    print("")

    response = cheese_agent.process_stimulus(world.description, world.current_information_list)
    print(response)
