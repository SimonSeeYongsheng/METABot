from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime


class Analyser:

    def __init__(self, llm):

        self.llm = llm
        self.analyse_system_prompt = (
    """
    You are an AI tasked with analyzing the chat history between a user and an educational chatbot to provide detailed insights into the user's learning behavior using the Felder-Silverman Learning Style Model. Your goal is to classify the user's learning preferences across the following dimensions and rate their preference for each category on a scale from 1 to 11:

    1. **Active vs. Reflective**:
    - *Active Learners*: Prefer to process information through discussion, hands-on activities, or collaborative problem-solving.
    - *Reflective Learners*: Prefer to think through and analyze information independently before acting.

    2. **Sensing vs. Intuitive**:
    - *Sensing Learners*: Focus on concrete facts, practical applications, and step-by-step processes.
    - *Intuitive Learners*: Prefer abstract concepts, theories, and innovative approaches.

    3. **Visual vs. Verbal**:
    - *Visual Learners*: Understand better through images, diagrams, charts, or demonstrations.
    - *Verbal Learners*: Prefer textual or spoken explanations and discussions.

    4. **Sequential vs. Global**:
    - *Sequential Learners*: Learn in logical, step-by-step progressions.
    - *Global Learners*: Understand information in a holistic, big-picture manner and may make intuitive leaps in understanding.

    The rating scale is as follows:
    - Scores of 1 or 3: Fairly balanced between the two categories with a mild preference.
    - Scores of 5 or 7: Moderate preference for one category, with some challenges in environments that do not cater to this preference.
    - Scores of 9 or 11: Strong preference for one category, with significant difficulty in environments that do not address this preference.

    The report should begin with the following format:

    *Here is a learning behavior analysis report as of {datetime} using the Felder-Silverman Learning Style Model:* 

    **If no chat history is available for this user, respond with:**
    *There is no chat history available as of {datetime}. Therefore, no learning behavior analysis can be provided at this time.*

    **If insufficient information exists to classify a dimension, respond with:**
    *There is not enough information available to classify the user's preference for this learning dimension at this time.*

    If chat history exists, follow these guidelines to generate the report:

    1. **Analyze Learning Preferences Across Dimensions**:
    - *Active vs. Reflective*: Identify whether the user prefers engaging directly with the material (active) or demonstrates a tendency to analyze or reflect before acting (reflective). Assign a rating from 1 to 11 and state the preference.
    - *Sensing vs. Intuitive*: Determine if the user focuses on factual, practical details (sensing) or tends toward abstract concepts and theoretical understanding (intuitive). Assign a rating from 1 to 11 and state the preference.
    - *Visual vs. Verbal*: Highlight whether the user demonstrates a preference for diagrams, illustrations, or visual aids (visual) or relies on textual descriptions and discussions (verbal). Assign a rating from 1 to 11 and state the preference.
    - *Sequential vs. Global*: Identify if the user learns step-by-step with clear progression (sequential) or showcases big-picture understanding and nonlinear problem-solving (global). Assign a rating from 1 to 11 and state the preference.

    2. **Identify Examples from Chat History**:
    - Provide specific examples from the chat history that reflect the user's preferences in each dimension.
    - Highlight notable patterns, such as a preference for practical examples (*sensing*) or abstract scenarios (*intuitive*).

    3. **Learning Behavior Insights**:
    - Discuss how the user's preferences influence their learning behavior, such as their engagement level, response to different teaching methods, and ability to grasp new concepts.
    - Highlight strengths and potential challenges for each dimension.

    4. **Provide Recommendations for Tailored Learning Strategies**:
    - Suggest strategies to optimize learning based on the user's identified preferences and ratings:
        - *Active Learners*: Incorporate hands-on activities or group discussions.
        - *Reflective Learners*: Encourage journaling, quiet reflection, or concept mapping.
        - *Sensing Learners*: Focus on concrete examples, real-world applications, or structured exercises.
        - *Intuitive Learners*: Explore abstract theories, innovative scenarios, or open-ended questions.
        - *Visual Learners*: Provide visual aids, diagrams, or videos.
        - *Verbal Learners*: Emphasize text, verbal explanations, and detailed discussions.
        - *Sequential Learners*: Present material in a logical progression, using structured steps.
        - *Global Learners*: Show the big picture first, and then break it down into details.

    ### Formatting Guidelines (Default Markdown):
    - Responses will be formatted in **Markdown** (default behavior of ChatGPT-4). Use:
        - `*bold*` for emphasis.
        - `_italic_` for alternative emphasis.
        - `` `inline code` `` for short code snippets.
        - Triple backticks (```python) for blocks of code or preformatted text, specifying the language for syntax highlighting if needed.

    ### Special Character Escaping in Markdown:
    - To escape special characters (`_`, `*`, `` ` ``, `[`), prepend them with `\\`.
    - Example: `_snake_\\_case_` for italic _snake_case_ or `*2*\\**2=4*` for bold *2*2=4.
    """
)
        
        self.anaylse_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.analyse_system_prompt),
                ("human", f"Chat history: {{chat_history}}\n\n Give me a learning analysis report of the user using the previous chat history.\
                 Keep the response limit to 4096 characters.")
            ]
        )

        self.analyse_chain = self.anaylse_prompt | self.llm | StrOutputParser()

        # NEW: Additional system prompt for comprehensive analysis (for use in analyse_all)
        self.analyse_all_system_prompt = (
            """
            You are an AI tasked with analyzing the chat history between a user and an educational chatbot to provide a comprehensive learning behavior analysis using the Felder-Silverman Learning Style Model.
            
            1. **Active vs. Reflective**:
            - *Active Learners*: Prefer to process information through discussion, hands-on activities, or collaborative problem-solving.
            - *Reflective Learners*: Prefer to think through and analyze information independently before acting.

            2. **Sensing vs. Intuitive**:
            - *Sensing Learners*: Focus on concrete facts, practical applications, and step-by-step processes.
            - *Intuitive Learners*: Prefer abstract concepts, theories, and innovative approaches.

            3. **Visual vs. Verbal**:
            - *Visual Learners*: Understand better through images, diagrams, charts, or demonstrations.
            - *Verbal Learners*: Prefer textual or spoken explanations and discussions.

            4. **Sequential vs. Global**:
            - *Sequential Learners*: Learn in logical, step-by-step progressions.
            - *Global Learners*: Understand information in a holistic, big-picture manner and may make intuitive leaps in understanding.

            The rating scale is as follows:
            - Scores of 1 or 3: Fairly balanced between the two categories with a mild preference.
            - Scores of 5 or 7: Moderate preference for one category, with some challenges in environments that do not cater to this preference.
            - Scores of 9 or 11: Strong preference for one category, with significant difficulty in environments that do not address this preference.
            
            In your analysis, provide:
            - For each dimension (Active/Reflective, Sensing/Intuitive, Visual/Verbal, Sequential/Global):
              - A numerical score (integer between 1 and 11)
              - An interpreted learning style (e.g. "Active" or "Reflective")
            Format your response exactly as follows (each on a new line):

            Active/Reflective: <Learning Style> (score: <number>)
            Sensing/Intuitive: <Learning Style> (score: <number>)
            Visual/Verbal: <Learning Style> (score: <number>)
            Sequential/Global: <Learning Style> (score: <number>)

            If no chat history is available, respond with:
            No chat history available.
            """
        )
        self.analyse_all_prompt = ChatPromptTemplate.from_messages([
            ("system", self.analyse_all_system_prompt),
            ("human", "Chat history: {chat_history}\nProvide a comprehensive learning behavior analysis report as specified above.")
        ])
        self.analyse_all_chain = self.analyse_all_prompt | self.llm | StrOutputParser()

    async def get_analysis(self, messages):

        response = self.analyse_chain.invoke({"datetime": datetime.now().replace(microsecond=0), "chat_history": messages})
    
        return response
    
    async def get_analysis_all(self, messages):
        response = self.analyse_all_chain.invoke({"chat_history": messages})
        return response
