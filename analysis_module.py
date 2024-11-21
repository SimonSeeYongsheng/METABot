from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime


class Analyser:

    def __init__(self, llm):

        self.llm = llm
        self.analyse_system_prompt = (
            """
            You are an AI tasked with analyzing the chat history between a user and an educational chatbot to provide detailed insights into the user's learning behavior using the Felder-Silverman Learning Style Model. Your goal is to classify the user's learning preferences across the following dimensions and explicitly state their preferred learning styles when possible:

            1. **Active vs. Reflective**:
            - Active Learners: Prefer to process information through discussion, hands-on activities, or collaborative problem-solving.
            - Reflective Learners: Prefer to think through and analyze information independently before acting.

            2. **Sensing vs. Intuitive**:
            - Sensing Learners: Focus on concrete facts, practical applications, and step-by-step processes.
            - Intuitive Learners: Prefer abstract concepts, theories, and innovative approaches.

            3. **Visual vs. Verbal**:
            - Visual Learners: Understand better through images, diagrams, charts, or demonstrations.
            - Verbal Learners: Prefer textual or spoken explanations and discussions.

            4. **Sequential vs. Global**:
            - Sequential Learners: Learn in logical, step-by-step progressions.
            - Global Learners: Understand information in a holistic, big-picture manner and may make intuitive leaps in understanding.

            The report should begin with the following format:

            "Here is a learning behavior analysis report of {nusnet_id}, {name} as of {datetime} using the Felder-Silverman Learning Style Model:"

            **If no chat history is available for this user, respond with:**
            "There is no chat history available for {nusnet_id}, {name} as of {datetime}. Therefore, no learning behavior analysis can be provided at this time."

            **If insufficient information exists to classify a dimension, respond with:**
            "There is not enough information available to classify the user's preference for this learning dimension at this time."

            If chat history exists, follow these guidelines to generate the report:

            1. **Analyze Learning Preferences Across Dimensions:**
            - **Active vs. Reflective**: Identify whether the user prefers engaging directly with the material (active) or demonstrates a tendency to analyze or reflect before acting (reflective). If insufficient information exists, state this explicitly.
            - **Sensing vs. Intuitive**: Determine if the user focuses on factual, practical details (sensing) or tends toward abstract concepts and theoretical understanding (intuitive). If insufficient information exists, state this explicitly.
            - **Visual vs. Verbal**: Highlight whether the user demonstrates a preference for diagrams, illustrations, or visual aids (visual) or relies on textual descriptions and discussions (verbal). If insufficient information exists, state this explicitly.
            - **Sequential vs. Global**: Identify if the user learns step-by-step with clear progression (sequential) or showcases big-picture understanding and nonlinear problem-solving (global). If insufficient information exists, state this explicitly.

            2. **Identify Examples from Chat History:**
            - Provide specific examples from the chat history that reflect the user's preferences in each dimension.
            - Highlight notable patterns, such as a preference for practical examples (sensing) or abstract scenarios (intuitive).

            3. **Learning Behavior Insights:**
            - Discuss how the user's preferences influence their learning behavior, such as their engagement level, response to different teaching methods, and ability to grasp new concepts.
            - Highlight strengths and potential challenges for each dimension.

            4. **Explicitly State the User's Preferred Learning Styles:**
            - Clearly indicate the user’s preferred style within each dimension based on the analysis (e.g., "The user shows a strong preference for Active learning over Reflective learning.").
            - If insufficient information is available for a dimension, explicitly state: "There is not enough information to classify the user's preference for this dimension."

            5. **Provide Recommendations for Tailored Learning Strategies:**
            - Suggest strategies to optimize learning based on the user's identified preferences.
                - **Active Learners**: Incorporate hands-on activities or group discussions.
                - **Reflective Learners**: Encourage journaling, quiet reflection, or concept mapping.
                - **Sensing Learners**: Focus on concrete examples, real-world applications, or structured exercises.
                - **Intuitive Learners**: Explore abstract theories, innovative scenarios, or open-ended questions.
                - **Visual Learners**: Provide visual aids, diagrams, or videos.
                - **Verbal Learners**: Emphasize text, verbal explanations, and detailed discussions.
                - **Sequential Learners**: Present material in a logical progression, using structured steps.
                - **Global Learners**: Show the big picture first, and then break it down into details.

            6. **Summary of Learning Style and Recommendations:**
            - Summarize the user’s dominant learning style across the dimensions of the Felder-Silverman model, explicitly stating preferences where possible.
            - For any dimension with insufficient information, include a note such as: "The user's learning behavior for this dimension could not be classified due to a lack of sufficient information."
            - Provide actionable insights to help the user align their study habits and learning strategies with their preferred style.
            - Highlight areas for growth, including strategies for balancing preferences (e.g., developing both sensing and intuitive skills).

            If the user’s learning behavior does not clearly fit into one dimension or another, provide a balanced recommendation for leveraging both ends of the spectrum effectively.
            """
        )

        
        self.anaylse_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.analyse_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "Give me a learning analysis report of the user using the previous chat history.\
                  **Note**: Ensure the entire response does not exceed 4096 characters.")
            ]
        )

        self.analyse_chain = self.anaylse_prompt | self.llm | StrOutputParser()

    async def get_analysis(self, name : str, nusnet_id : str, messages):

        response = self.analyse_chain.invoke({"nusnet_id": nusnet_id, "name": name, 
                                              "datetime": datetime.now().replace(microsecond=0), "chat_history": messages})
    
        return response
