import logging 

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from google.api_core import exceptions




class SkillMatch(BaseModel):
    skill: str = Field(description="The skill being evaluated")
    match_level: str = Field(description="How well the skill matches: High/Medium/Low/Not Found")
    explanation: str = Field(description="Explanation of the match level")



class JobFitAnalysis(BaseModel):
    overall_match_percentage: int = Field(description="Overall match percentage 0-100")
    summary: str = Field(description="Overall summary of the match")



class JobFitAnalyzer:
    def __init__(self, llm):
        cleaning_prompt = ChatPromptTemplate.from_template(
            """
            The following is text scraped from a webpage for a job description. 
            It has a lots of junk words, please remove all junk words and keep only the job description: 
            Job description: {job_description} 
            """
        )
        self._cleaning_chain = (
            ( lambda job_description: {"job_description": job_description})
            | cleaning_prompt
            | llm        
        )

        self._output_parser = PydanticOutputParser(pydantic_object=JobFitAnalysis)
        analyzer_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert hiring manager and resume analyst. 
            Analyze the provided resume and the job seeker's preferences
            against the job description to determine fit.
            Be thorough but fair in your analysis.

            Focus on:
            1. Technical skills match
            2. Experience level alignment
            3. Role-specific requirements
            4. Soft skills where mentioned
            5. Industry experience
            6. Whether this role matches the job seeker's preferences.

            Provide your analysis in a structured format.
            {format_instructions}"""),
            ("user", """Job Description:
            {job_description}

            Here is what the job seeker's preferences for their next role:
            {job_preferences}
            
            Here is their resume:
            {resume}
            
            Please analyze the fit between this resume, job preferences, and job description.""")
        ])
        self._analysis_chain = (
            analyzer_prompt
            | llm
            | (lambda output: output.content)
            | self._output_parser
        )


    def analyze_fit(self, job_description: str, job_preferences: str, resume: str) -> str:
        """Analyze how well a resume matches a job description."""
        # Get the response from the LLM
        try:
            parsed_response = self._analysis_chain.invoke({
                'format_instructions': self._output_parser.get_format_instructions(),
                'job_description': self._cleaning_chain.invoke(job_description),
                'job_preferences': job_preferences,
                'resume': resume
            })
            logging.debug(f"Parsed response: {parsed_response}")
        
            return parsed_response
        except Exception as e:
            logging.error(e)
            pass
