import logging
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List



class SkillMatch(BaseModel):
    skill: str = Field(description="The skill being evaluated")
    match_level: str = Field(description="How well the skill matches: High/Medium/Low/Not Found")
    explanation: str = Field(description="Explanation of the match level")



class JobFitAnalysis(BaseModel):
    overall_match_percentage: int = Field(description="Overall match percentage 0-100")
    summary: str = Field(description="Overall summary of the match")



class JobFitAnalyzer:
    def __init__(self, llm):
        self._llm = llm        
        self._output_parser = PydanticOutputParser(pydantic_object=JobFitAnalysis)
        self._prompt = ChatPromptTemplate.from_messages([
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


    def analyze_fit(self, job_description: str, job_preferences: str, resume: str) -> str:
        """Analyze how well a resume matches a job description."""
        formatted_prompt = self._prompt.format_messages(
            format_instructions=self._output_parser.get_format_instructions(),
            job_description=job_description,
            job_preferences=job_preferences,
            resume=resume
        )
        
        # Get the response from the LLM
        try:
            response = self._llm.invoke(formatted_prompt).content
            parsed_response = self._output_parser.parse(response)
        
            return parsed_response
        except:
            pass
