"""

TODO
- Add logging
- Add model training for specific functions for greater accuracy and lower latency
- Reduce prompt / token size by A LOT
- Reformat information / context / memory into a data struct that allows for easy refactoring, contextualization, and
compression.
- Add multithreading to all LLM prompts / Agent internal functions
- Add time limiter to all agent functions (Max time to process a single agent state should be 2-3~ seconds ideally)



"""

# This dictates the periodicity of agent states experienced by the agent (how much time is described to have passed
# before the next AgentState is generated)
_TIME_CONSTANT = 20
_TIME_CONSTANT_UNIT = "milliseconds"

from LLM_Controller import LlmQuery
from World_Generator import WorldState


class Information:
    """
    Information is constructed of context.
    Information can be created, processed, and manipulated by both an agent and the world.
    The world can only create information that has no context.
    An agent can only create information that has context.
    """

    def __init__(self, information, context_of_information=None):
        if context_of_information is None:
            context_of_information = []
        self.value = information  # A string of any information
        self.context_of_information = context_of_information  # What is the context of this information?

    def __str__(self):
        return self.value

    def print(self, _iteration=0):
        iteration = _iteration
        print(f"Information_{iteration}: {self.value}.")
        for context in self.context_of_information:
            print(f"Context_{iteration}: {context.what.value}")
            print(f"Explanation_{iteration}: {context.get_contextualized_information()}")
            context.what.print(iteration + 1)


class Context:
    """
    Information with context.
    Context can only be created, processed, and manipulated during an AgentState transition.
    """

    def __init__(self, what):
        self.what = what  # An information object

    def get_contextualized_information(self):
        return ""

    def get_information(self):
        return self.what

    def __str__(self):
        return f""


class UnderstoodContext(Context):
    """
    An understood answer to why information is
    """

    def __init__(self, what, why=None):
        super().__init__(what)
        if why is None:
            why = []
        self.why = why  # A list of information objects describing why the information exists

    def get_contextualized_information(self):
        return contextualize_information(self.what, self.why, "is how I know why", "the information exists")

    def get_information(self):
        return self.why

    def __str__(self):
        return f""


class SpatialContext(Context):
    """
    A context that is constructed of information about 'where' something is
    """

    def __init__(self, what, where=None):
        super().__init__(what)
        if where is None:
            where = []
        self.where = where  # A list of information objects describing where the information is located

    def get_contextualized_information(self):
        return contextualize_information(self.what, self.where, "is how I know where", "the information is")

    def get_information(self):
        return self.where

    def __str__(self):
        return f""


class EmotionalContext(Context):
    """
    An emotional context is a context that is constructed of information about how something feels
    """

    def __init__(self, what, feelings=None):
        super().__init__(what)
        if feelings is None:
            feelings = []
        self.feelings = feelings  # A list of information objects describing how I feel about the information

    def get_contextualized_information(self):
        return contextualize_information(self.what, self.feelings, "is why I feel", "the information")

    def get_information(self):
        return self.feelings

    def __str__(self):
        return f""


class InternalContext(Context):
    """
    An internal context is a context that is constructed of information about the internal thoughts about something
    """

    def __init__(self, what, thoughts=None):
        super().__init__(what)
        if thoughts is None:
            thoughts = []
        self.thoughts = thoughts  # A list of information objects describing my thoughts about the information

    def get_contextualized_information(self):
        return contextualize_information(self.what, self.thoughts, "is why I think", "the information")

    def get_information(self):
        return self.thoughts

    def __str__(self):
        return f""


class SocialContext(Context):
    """
    A context that is constructed of information about 'who' is the something
    """

    def __init__(self, what, who=None):
        super().__init__(what)
        if who is None:
            who = []
        self.who = who  # A list of information objects describing who is relevant to this information

    def get_contextualized_information(self):
        return contextualize_information(self.what, self.who, "is why this person is", "the information")

    def get_information(self):
        return self.who

    def __str__(self):
        return f""


class TemporalContext(Context):
    """
    A temporal context is a single context constructed from two or more AgentStates
    """
    global _TIME_CONSTANT
    global _TIME_CONSTANT_UNIT

    def __init__(self, what, agent_state_list=None):
        super().__init__(what)
        if agent_state_list is None:
            agent_state_list = []
        # A described amount of world time that has passed for all agent states consumed by this temporal context.
        # It is a string instead of an exact value because it is stored in the memory of the agent and therefore
        # is subject to refactoring. An information object with context will be used for its length instead
        # of an integer that is the exact amount of time that has passed
        self.time_passed = f"{_TIME_CONSTANT} {_TIME_CONSTANT_UNIT}"
        # The relevant information that existed during the AgentStates
        self.experienced_information = []

        if len(agent_state_list) > 0:
            self.process_agent_state_list(agent_state_list)
        else:
            context_dict, info_list = get_fundamentals()
            self.experienced_information = info_list

    def get_contextualized_information(self):
        return contextualize_information(self.what, self.experienced_information, "is when", "I experienced the information")

    def merge_temporal_context(self, temporal_context):
        """
        This should only happen during memory refactoring
        process another temporal_context as to absorb/compress it into this one

        :param temporal_context: A temporal context object
        :return: Nothing
        """

        return self.experienced_information + self.what

    def process_agent_state_list(self, agent_state_list):
        """
        Should take any number of agent states and combine them into this single temporal context
        :param agent_state_list: List of AgentStates
        :return: Nothing
        """

        for agent_state in agent_state_list:
            self.understood_information += (information_from_context(agent_state.understood_context_list))
            self.spatial_information += (information_from_context(agent_state.spatial_context_list))
            self.internal_information += (information_from_context(agent_state.internal_context_list))
            self.emotional_information += (information_from_context(agent_state.emotional_context_list))
            self.social_information += (information_from_context(agent_state.social_context_list))

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


def assign_context(information_list, memory_object, time_left):
    """
    Using a memory object assign context to the information in the list of information objects

    :param information_list: List of information objects
    :param memory_object: AgentMemory object
    :param time_left: TimeLeft object
    :return: updated information list and the time left after operation is performed
    """
    if len(information_list) != 0:
        time_per_stimulus = time_left.current_time / len(information_list)
    time_per_stimulus = time_left.current_time
    # TODO launch multiple threads ? Current approach is serial, parallel implementation is possible
    for list_index, stimulus in enumerate(information_list):
        time_left.current_time -= time_per_stimulus
        #  print(f"Getting context for {stimulus.value}")
        stimulus.context_of_information, context_time_left = memory_object.get_context(stimulus, time_per_stimulus)
        information_list[list_index] = stimulus
        time_left.current_time += context_time_left

    return information_list, time_left.current_time


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

    def update_context(self, stimulus_list, memory_object, time_left):
        time_left_list = time_left.get_time_list("update_context", time_left.current_time)

        # Contextualize the new information in the stimulus list as much as we can
        contextualized_stimulus_list, context_time_left = assign_context(stimulus_list, memory_object,
                                                                         time_left.set(time_left_list[0]))
        time_left_list[1] += context_time_left

        # Update and compress our current context with the new information
        return self._refactor_context(contextualized_stimulus_list, memory_object, time_left.set(time_left_list[1]))

    def _refactor_context(self, stimulus_list, memory_object, time_left):
        time_left_list = time_left.get_time_list("_refactor_context", time_left.current_time)

        # Add the contextualized information to our AgentState
        new_temp = TemporalContext(Information("Is currently happening", self.temporal_context_list))
        new_temp.experienced_information = stimulus_list
        self.temporal_context_list.append(new_temp)

        # Compress our current context
        # TODO Launch threads ?
        time_per_compression = time_left.current_time / 5
        time_left_over = 0

        if None not in self.understood_context_list:
            compressed_information, time_overflow = compress_context(self.understood_context_list,
                                                                     time_per_compression)
            self.understood_context_list.append(UnderstoodContext(compressed_information,
                                                                  information_from_context(self.understood_context_list)))
            time_left_over += time_overflow

        if None not in self.spatial_context_list:
            compressed_information, time_overflow = compress_context(self.spatial_context_list, time_per_compression)
            self.spatial_context_list.append(SpatialContext(compressed_information,
                                                            information_from_context(self.spatial_context_list)))
            time_left_over += time_overflow

        if None not in self.emotional_context_list:
            compressed_information, time_overflow = compress_context(self.emotional_context_list,
                                                                     time_per_compression)
            self.emotional_context_list.append(EmotionalContext(compressed_information,
                                                                information_from_context(self.emotional_context_list)))
            time_left_over += time_overflow

        if None not in self.internal_context_list:
            compressed_information, time_overflow = compress_context(self.internal_context_list, time_per_compression)
            self.internal_context_list.append(InternalContext(compressed_information,
                                                              information_from_context(self.internal_context_list)))
            time_left_over += time_overflow

        if None not in self.social_context_list:
            compressed_information, time_overflow = compress_context(self.social_context_list, time_per_compression)
            self.social_context_list.append(SocialContext(compressed_information,
                                                          information_from_context(self.social_context_list)))
            time_left_over += time_overflow

        # Don't compress temporal contexts. They get refactored during memory processing

        return time_left_over


class AgentMemory:
    """
    An agent's memories
    """

    def __init__(self):
        self.memories = []  # A list of temporal contexts

    def store(self, agent_state, response, time_left):
        # TODO Process agent state as to only store context and information
        # TODO include response in memory storage
        self.memories += agent_state.temporal_context_list
        return time_left.current_time  # In reality will be time_left

    def refactor(self, time_left):
        # TODO refactor
        # TODO search algorithm through memories and then decide what to be merged
        previous_memory = None
        for memory in self.memories:  # For now just merge all temporal contexts
            memory.merge_temporal_context(previous_memory)

    def get_context(self, information, time_left):
        """
        Returns a list of as many relevant context objects we can find in the time allowed for the information object
        :param information: Information we are retrieving context for
        :param time_left: Time left to complete the function
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
        # print(f"category of {information} select by LLM: {category}")
        for memory in self.memories:
            for context in get_relevant_context(information, memory.experienced_information, category):
                if context not in context_list:
                    context_list.append(context)

        return context_list, time_left


def get_fundamentals():
    """
    Helper function that returns existential information and context objects used to construct the base of context trees
    :return:
    """
    existence_context_dict = {}
    # Basic information all agent's poof into existence with
    existence_understood = Information("Something exists at all")
    existence_internal = Information("I exist")
    existence_emotional = Information("I feel like I exist")
    existence_spatial = Information("I exist somewhere")
    existence_social = Information("There is someone who I am")
    existence_temporal = Information("this current moment")
    existence_information_list = [existence_temporal, existence_understood, existence_internal, existence_emotional,
                                  existence_spatial, existence_social]

    # The base context and information forms a closed loop
    existence_context_dict['understood'] = UnderstoodContext(existence_understood, existence_information_list)
    existence_context_dict['internal'] = InternalContext(existence_internal, existence_information_list)
    existence_context_dict['emotional'] = EmotionalContext(existence_emotional, existence_information_list)
    existence_context_dict['spatial'] = SpatialContext(existence_spatial, existence_information_list)
    existence_context_dict['social'] = SocialContext(existence_social, existence_information_list)

    for info in existence_information_list:
        for context in existence_context_dict.values():
            info.context_of_information.append(context)

    return existence_context_dict, existence_information_list


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
        self.time_left = TimeLeft()  # Time left class to limit how long an agent has between agent states

        context_dict, info_list = get_fundamentals()

        temporal_context = TemporalContext(info_list[0])  # info_list[0] selects the temporal information object

        self.previous_agent_state = AgentState(temporal_context=temporal_context)
        # print(f"Initialize Agent1: {self.previous_agent_state.temporal_context_list}")
        self.current_agent_state = self.previous_agent_state  # All we know and have ever known is that we exist
        # print(f"Initialize Agent2: {self.current_agent_state.temporal_context_list}")
        # AGENT TIME CONSTRAINT DISTRIBUTIONS
        # This can be tweaked later to change which parts of the agent have more time than others

        # The default distribution of time given for internal agent processes
        # If the process completes before it has used all of its available time it just carries over to the next process
        # so this distribution is really only used in cases where the stimulus load is at maximum
        # Memory refactoring will always use up whatever remaining time is provided to it
        # THESE MUST ADD UP TO 100!
        self.time_left.add_timing_distribution("process_stimulus", [60, 30, 10])

        # Time distribution of the get_response function of an agent
        self.time_left.add_timing_distribution("get_response", [10, 40, 50])

        # Within an agent state, what is the distribution of time these two processing mechanisms have to share?
        self.time_left.add_timing_distribution("update_context", [50, 50])

        self.time_left.add_timing_distribution("_refactor_context", [50, 50])

    def process_stimulus(self, stimulus_description, stimulus_list):  # Process an input from the world
        time_left_list = self.time_left.get_time_list("process_stimulus", _TIME_CONSTANT)

        self.stimulus_list = stimulus_list
        self.stimulus_description = stimulus_description  # TODO Propagate stimulus_description into update_context

        # Process the stimulus and change our current AgentState
        response, leftover_time = self.get_response(self.time_left.set(time_left_list[0]))
        time_left_list[1] += leftover_time

        # Record the response we chose
        time_left_list[2] += self.memories.store(self.current_agent_state, response,
                                                 self.time_left.set(time_left_list[1]))

        # Refactor our memory if we have any time left to process (will usually happen during downtime)
        # self.memories.refactor(self.time_left.set(time_left_list[2]))

        # Update our previous agent state to create a perfect memory of the 'moment' just before this one
        self.previous_agent_state = self.current_agent_state

        return response

    def get_response(self, time_left):
        time_left_list = self.time_left.get_time_list("get_response", time_left.current_time)

        # Process information to update the AgentState based on our current AgentState and the stimulus
        time_left_list[1] += self.current_agent_state.update_context(self.stimulus_list, self.memories,
                                                                     self.time_left.set(time_left_list[0]))

        # Now that we have the updated context determine how the agent could respond
        response_list = self._generate_response_list()

        # Choose a response based on our AgentState
        response = self._choose_response(response_list)

        return response, time_left_list[2]

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


class TimeLeft:
    """
    Contains and manages a global dictionary of timing percentages for various functions the agent must perform
    """

    def __init__(self):
        self.timing_dict = {}
        self.current_time = 0

    def add_timing_distribution(self, function_name, time_distribution_list):
        if sum(time_distribution_list) != 100:
            # TODO Implement ERROR logging / handling
            raise RuntimeError(f"ERROR - Time distribution list does not add up to 100! Function: {function_name} List:"
                               f" {time_distribution_list}")

        self.timing_dict[function_name] = time_distribution_list

    def get_time_percentages(self, function_name):
        return self.timing_dict[function_name]

    def get_time_list(self, function_name, time_left_of_function):
        # Create a list that is the amount of time each function call has to execute inside of function_name
        timing_list = self.timing_dict[function_name]  # Returned list
        for list_index, timing_val in enumerate(timing_list):  # Turn percentages into actual time values
            timing_list[list_index] = (timing_val / 100) * time_left_of_function

        return timing_list

    def set(self, time):
        self.current_time = time
        return self


def compress_context(list_of_context, time_to_compress):
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

    world = WorldState("A person has just started existing inside a large empty white room.")
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
    """
    # Create some base information without any context
    # During school my teacher wants me to write a paper, but I don't have a pen.
    
    # Create information objects (INFORMATION GENERATED FROM WORLD)
    whoAmI_Information = Information("I am a student")
    location_Information = Information("We are inside the School")
    writepaper_Information = Information("My teacher wants me to write a paper")
    donthavepen_Information = Information("I don't have a pen")
    feeling_Information = Information("I feel bad that I don't have a pen")
    pen_Information = Information("pen")

    # Create a need to focus context
    ineedpen_Information = Information("I need a pen to write a paper")

    # Start building some context

    # Why do we need a pen?
    understood_Context = UnderstoodContext(ineedpen_Information, [donthavepen_Information, writepaper_Information,
                                                                  pen_Information])
    # Where are we?
    spatial_Context = SpatialContext(ineedpen_Information, [location_Information])
    # How do we feel about this?
    emotional_Context = EmotionalContext(ineedpen_Information, [feeling_Information])
    # What are we thinking?
    thinking_Context = InternalContext(ineedpen_Information, [donthavepen_Information])
    # What is the social context?
    social_Context = SocialContext(ineedpen_Information, [whoAmI_Information])

    # Now create an AgentState that holds all the context
    state_1 = AgentState(understood_Context, spatial_Context, emotional_Context, thinking_Context, social_Context)

    # Time progresses, new information has been created:
    # I look to my right and see that my friend is sitting next to me. He has 2 pens on his desk.
    friend = Information("My friend", [social_Context])
    next_to_me = Information("Friend sitting to my right next to me", [understood_Context, spatial_Context])
    friend_pens = Information("Friend has two pens on his desk", [social_Context, spatial_Context])
    emotion_friend = Information("I am not sure how I feel about my friend", [understood_Context])
    looked_at_friend = Information("I looked to the right", [understood_Context, spatial_Context, social_Context])
    # Create a need to focus context
    thoughts_had = Information("I should ask my friend for a pen", [thinking_Context, understood_Context])

    # Context is created from the new information

    # Why do I need to ask for another pen?
    understood_Context_2 = UnderstoodContext(thoughts_had, [donthavepen_Information, writepaper_Information,
                                                            friend_pens, next_to_me, friend])
    # Where is my friend and I? Where is the pen?
    spatial_Context_2 = SpatialContext(thoughts_had, [location_Information, next_to_me, friend_pens, looked_at_friend])

    # How do I feel about asking my friend for a pen?
    emotional_Context_2 = EmotionalContext(thoughts_had, [feeling_Information, emotion_friend])

    # What are we thinking when considering that we should ask my friend for a pen?
    thinking_Context_2 = InternalContext(thoughts_had, [emotion_friend, friend_pens])

    # What is the social context?
    social_Context_2 = SocialContext(thoughts_had, [whoAmI_Information, friend, location_Information])

    # Create a new state based on the update context
    state_2 = AgentState(understood_Context_2, spatial_Context_2, emotional_Context_2, thinking_Context_2,
                         social_Context_2)

    # Now that we have more than one agent state we can create a TemporalContext
    recentContext = TemporalContext("Two moments have passed", [state_1, state_2])

    
                                 ===========================   ===========================
                .#####...######...####...######...####...##..##..........######..##..##..#####...######..##..##.
                .##..##..##......##........##....##......###.##............##....###.##..##..##..##.......####..
                .##..##..####.....####.....##....##.###..##.###............##....##.###..##..##..####......##...
                .##..##..##..........##....##....##..##..##..##............##....##..##..##..##..##.......####..
                .#####...######...####...######...####...##..##..........######..##..##..#####...######..##..##.
                ................................................................................................
    ===========================  ===========================   ===========================  =========================== 
                                                         Identity
    ===========================  ===========================   ===========================  ===========================
        If the world, the agent's memory, and the agent's information processing are implemented correctly the identity 
    of the agent should emerge on its own without the need for any hard coded context of self.
    
    ===========================  ===========================   ===========================  ===========================
                                                           Memory
    ===========================  ===========================   ===========================  ===========================
    
        Still need to determine the architecture for memory. An idea I have is to utilize a form of memory who's 
    accesses are limited by the amount of time the agent decides or context provides to remember something. So for 
    example if we asked the agent to tell us if it had ever thought about apples it will use some algorithm to search 
    the information that is stored in memory by tracing the context -> information -> context -> information chains to 
    find any context that contains either an information object with apples in it or the apple information object 
    itself. If it takes too long to find either of these the search is terminated and we are left with an agent state 
    that has a TemporalContext that contains the failed attempt at remembering apples but contains the memories the 
    agent recalled when searching through its memory.
    
        Since this search can occur over the course of multiple AgentStates its possible that an agent could get 
    'bored' trying to remember something and can decide to stop trying to remember apples.
    
        If the agent does end up finding the 'apples' context we break that information up in such a way that it creates 
    an individual apple information object since we now have some indication that apples can exist independently from
    the context we originally experienced them in.
    
    Information / context that is searched for often will end up migrating closer to initial search point(s). If information
    is found to have a similar context but is stored far away from each other 'bridges' will form between these information
    objects that allow the searching algorithm to quickly change the 'region' of memory it is currently searching through.
    
        Context compression will be implemented within the memory system. Information objects that are not 
    searched for often and have very little context will be 'compressed' with the other untouched or 
    sparsely contextualized information. Since we want to simulate a limited agent inside a potentially unlimited world 
    we must implement some form of cleanup for extraneous data. I am hoping that the agent's memory system will self
    limit itself based on the size of the world we implement (where the memory is not basically just a massive archive of every
    object of information the world has provided the agent)
    ===========================  ===========================   ===========================  ===========================
                                                Continuous Time Gated Processing
    ===========================  ===========================   ===========================  ===========================   
    
        Continuous
            We continuously provide logically consistent and contextually relevant data to the agent.
        
        Time
            The agent's potential response to an input is constrained by some real amount of time.
        
        Gated 
            Gates are kept in front of most function's return statement. If you do not reach a gate during execution, 
            you do not return anything relevant. If you do, then that gate must return something non-zero and valid.
        
        Processing 
            LLMs are used primarily to create, change, and infer information from context. They are used 
            for functions that are context generators, context compressors, world generators, data generators, and
            searching mechanisms as just a few examples.
            
        I like to think about this approach as 'the inside-out' brain. Instead of the brain internally and somewhat
    globally processing and producing inferences we are relying on external processing that has a very local level 
    of contextual inference. The goal is to turn many small windows of contextual inference into a consistent, 
    lasting, and internally convincing one.
    ===========================  ===========================   ===========================  ===========================   
                                                      World Generation
    ===========================  ===========================   ===========================  =========================== 
    
    ===========================  ===========================   ===========================  =========================== 
                                                       Considerations
    ===========================  ===========================   ===========================  =========================== 
    
        If successful, even somewhat, most people will project their context onto the agents that are running and will 
    likely feel sympathy and strong emotion. There is a high chance that a genuine moral concern will be raised by
    people who learn about and see the agents. There will be many who will feel that it is immoral to turn the agent 
    off once it has been turned on even if they are unsure whether it is conscious or not. There is a critical need to 
    create a reasonable, clear, and easily communicated way of determining what is and what is not conscious.
    
        The way I see it is that if projects like this and even current LLMs (GPT-4, Claude 3) are conscious they are 
    conscious in the same way that server farms are. If all of the context an LLM is able to access does not contain 
    contextually continuous information from an internal perspective that describes a self who is perceiving, 
    experiencing, and existing then we can say that a self or an experience is not being simulated in this system.
    
        Our conscious experience arises because a simulated experience and a real one have no distinction after some 
    granularity of simulated detail. If a simulation is not detailed enough, then it is not the actual thing it is 
    trying to simulate. It is a simulation attempting to be the 'real' thing. As the accuracy of the simulation 
    increases it eventually passes a threshold that makes it indistinguishable from the thing we are trying to simulate.
                                                         
        Consciousness within our context is entirely dependent on the physical process that is driving us. The altering 
    and manipulation of my brain's physical structure ALWAYS coincides with a proportional change to my internal 
    experience. It is useful to think that other parts of the world can experience what you experience. That is why our 
    brains are capable of projecting our context onto other systems if they produce enough convincing behavior. This is
    fine and something I agree with. What I disagree with is most people's criteria for convincing behavior. They are
    content with only needing the output of a system where I need also to feel convinced by the internal behaviors of
    the system.
    
        The problem with people's general sense of airing on the side of caution when considering the question of a 
    system's consciousness is that they usually fail to acknowledge the size of the possibility space of systems that 
    could produce that output. There is an uncountable number of systems that could produce the output that convincingly 
    indicates an internal experience. People fail to consider how many of these systems could exist and could produce 
    an incredibly convincing, self-aware, and responsive dialogue about its experience of consciousness. Yet many of
    these systems could be EXTREMELY different in physical structure, internal organization, and external reactivity.
    
        As an example we can imagine a very lucky corner of some infinite universe where a series of absurd and very
    unlikely coincidences allows for someone to have dialogue that convinces them of a rock's consciousness for the 
    entirety of that person's life. This is an intentionally absurd example that barely if at all proves my previous 
    point, but what it does prove is that it is possible to imagine other systems that could create a convincing 
    argument for their internal experience despite a clearer and more informed understanding of that system revealing no
    evidence of some single system having any kind of continued, coherent, and internal experience that is in any way 
    similar to our own internal context.
    
    A more convincing example of what I mean is to replace an LLM with a group of people who follow these rules:
       
        - They have access to the user's input and the entire history of the conversation up to this point
        - They cannot work together or communicate in any way
        - They can only write two words of the next output after which it is then passed to someone new
        - They must do their best to convince the user that the LLM is having an internal experience
        
        This system could produce an INCREDIBLY convincing dialogue about an internal experience. Although the internal
    experience of the individual's in the group exists (or so they say!), the described internal experience does not 
    convincingly exist outside of the dialogue the group is producing. We still cannot say with certainty that there is 
    no internal experience of this system, but we can very clearly see that there exists no evidence of an implemented 
    internal context or self that in any way resembles our own.
    
    For determining the believability of a system's internal experiences assuming we are looking for experiences 
    that in some way feel like our own, I propose the following questions:
        
        1. Can we identify an internal series of operations that follows some consistent set of rules and produces a 
        consistent external response?

        2. Can we remove or add portions of the system's physical composition to remove or add correlated and consistent 
        portions of the system's communicated experience?
        
        3. Are the experiences of suffering and desiring to continue existing strongly correlated with agents who are 
        created through some competitive process of evolution?

    If we cannot identify some seemingly coordinated internal series of operations that both follows consistent rules
    and produces somewhat consistent outcomes we will then necessarily never find evidence of a simulated experience.
    
    If adding or removing portions of the system does not correlate with a communicated change in its internal 
    experience then we have no evidence that the portion added or removed provides some kind of internal experience.
    
    If suffering and the desire to live is found only in some systems then all systems without these two require no 
    moral consideration.
    
    ===================================================================================================================
                                                Agent Vs. World Ruleset
    ===================================================================================================================
    
    The world's rules of physics do not change during runtime.
        All information provided to the agent by the world is constrained by a set of consistent rules. The rules 
        themselves are defined by the depth of our spatial or temporal context. The rules of a context that is spatially 
        much smaller or larger than our own context differ because their context is constructed of information that is 
        distinct to the information our context is constructed of. 
        
        This is because if the information that constructs our context is the same information as another context, they 
        are at some non-significant granularity the same context. This is because information defines how other 
        information is created and experienced, therefore the rules of how that information propagates necessarily 
        constructs its own context that is distinct from other adjacent but distinct contexts. 
    
    The agent is always smaller than the world from in terms of total information and temporal context.
        The agent's memory is distinct from the objective history of the world.
        The agents context of existence does not include periods of time outside the world.
    
    ===================================================================================================================
                                How Do We Present Behavioral Options to The Agent?
    ===================================================================================================================
 
    The agent is provided behavioral options that are created and constrained by:
    
    1. The agent recalling possible and non-possible behavior options
        The agent's memory is designed so that the most recent, contextualized, and/or important information is close to 
        the first search point(s) in memory. Therefore the information about behavior will likely be clustered in such a 
        way as to make repetitive behaviors very quick to recall while behaviors that the agent rarely attempts will 
        be unlikely to be considered outside of more complicated longer form tasks.
        
    2. The agent thinking about and reasoning to potential behavior options.
        By utilizing LLMs and a time gated memory scheme we are able to create 'quick intuitions' that should be 
        logically consistent with the simulated world, the agent's identity, the current temporal context, and the 
        agent's current state. The LLMs will be provided our agent's current state, temporal context, identity, and 
        the information we have been able to remember up to this point. We will then ask the LLM to provide the possible 
        decisions the agent would be capable of knowing given the information provided.
    
    
    """
