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
    def __init__(self, llm, cleaning_prompt_path="res/cleaning_prompt.txt",
                 analysis_prompt_path="res/analysis_prompt.txt"):
        with open(cleaning_prompt_path,'r') as f:
            cleaning_prompt_text = f.read()
        cleaning_prompt = ChatPromptTemplate.from_template(cleaning_prompt_text)
        self._cleaning_chain = (
            (lambda job_description: {"job_description": job_description})
            | cleaning_prompt
            | llm        
        )

        with open(analysis_prompt_path,'r') as f:
            analysis_prompt_text = f.read()
        self._output_parser = PydanticOutputParser(pydantic_object=JobFitAnalysis)
        self._analyzer_prompt = ChatPromptTemplate.from_template(analysis_prompt_text) 
        self._analysis_chain = (
            self._analyzer_prompt
            | llm
            | (lambda output: output.content)
        )


    def analyze_fit(self, job_description: str, job_preferences: str, resume: str) -> str:
        """Analyze how well a resume matches a job description."""
        # Get the response from the LLM
        try:
            input_args = {
                'format_instructions': self._output_parser.get_format_instructions(),
                'job_description': self._cleaning_chain.invoke(job_description).content,
                'job_preferences': job_preferences,
                'resume': resume
            }
            response = self._analysis_chain.invoke(input_args)
            parsed_response = self._output_parser.invoke(response)
            logging.debug(f"Parsed response: {parsed_response}")

            output = {
                "prompt": self._analyzer_prompt.format(**input_args),
                "response": response,
                "parsed_response": parsed_response
            }
            return output
        except Exception as e:
            logging.error(e)
            pass
