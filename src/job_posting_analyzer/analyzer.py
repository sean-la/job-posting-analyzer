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
    key_matches: List[SkillMatch] = Field(description="List of key skill matches")
    missing_skills: List[str] = Field(description="Important skills from job description not found in resume")
    recommendations: List[str] = Field(description="Specific recommendations for the candidate")
    remote_in_canada: bool = Field(description="Whether this role can be performed remote in Canada")
    summary: str = Field(description="Overall summary of the match")



class JobFitAnalyzer:
    def __init__(self, llm):
        self._llm = llm        
        self._output_parser = PydanticOutputParser(pydantic_object=JobFitAnalysis)
        
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert hiring manager and resume analyst. 
            Analyze the provided resume against the job description to determine fit.
            Be thorough but fair in your analysis.
            The job seeker lives in Canada, so roles that can be performed remote in Canada
            are perferred.
            
            Focus on:
            1. Technical skills match
            2. Experience level alignment
            3. Role-specific requirements
            4. Soft skills where mentioned
            5. Industry experience
            6. Whether this role can be performed remotely in Canada
            
            Provide your analysis in a structured format.
            {format_instructions}"""),
            ("user", """Job Description:
            {job_description}
            
            Resume:
            {resume}
            
            Please analyze the fit between this resume and job description.""")
        ])

    def _format_analysis(self, analysis: JobFitAnalysis) -> str:
        """Format the analysis results into a readable string."""
        output = [
            f"Overall Match: {analysis.overall_match_percentage}%\n",
            "\nKey Skill Matches:",
        ]

        for skill in analysis.key_matches:
            output.append(f"\n- {skill.skill} (Match Level: {skill.match_level})")
            output.append(f"  {skill.explanation}")

        if analysis.missing_skills:
            output.append("\nMissing Skills:")
            for skill in analysis.missing_skills:
                output.append(f"- {skill}")

        output.append("\nRecommendations:")
        for rec in analysis.recommendations:
            output.append(f"- {rec}")

        output.append(f"\nRemote in Canada:\n{analysis.remote_in_canada}")

        output.append(f"\nSummary:\n{analysis.summary}")

        return "\n".join(output)

    def analyze_fit(self, job_description: str, resume: str) -> str:
        """Analyze how well a resume matches a job description."""
        formatted_prompt = self._prompt.format_messages(
            format_instructions=self._output_parser.get_format_instructions(),
            job_description=job_description,
            resume=resume
        )
        
        # Get the response from the LLM
        try:
            response = self._llm.invoke(formatted_prompt).content
            parsed_response = self._output_parser.parse(response)
        
            return parsed_response
        except:
            pass



class JobDuplicateRemover:

    def __init__(self, llm):
        self._llm = llm

        self._prompt = ChatPromptTemplate.from_messages([
            (
                "system", 
                """
                You will be given a list of jobs, but some of them will likely be duplicates.
                Please remove duplicates, and output the list of jobs in the same format as was given
                to you.
                """
            ),
            (
                "user", 
                """
                Job List:
                {job_list}
            
                Please remove duplicates from this list of jobs, and output them in the same
                format as was given to you.
                """
            )
        ])

    def remove_job_duplicates(self, job_list: str):
        formatted_prompt = self._prompt.format_messages(
            job_list=job_list
        )
        try:
            response = self._llm.invoke(formatted_prompt).content
            return response
        except:
            pass


def main():
    # Initialize analyzer with your OpenAI API key
    job_description = ""
    resume = ""
    model = None
    analyzer = JobFitAnalyzer(model)
    
    # Analyze the fit
    analysis = analyzer.analyze_fit(job_description, resume)
    print(analysis)



if __name__ == "__main__":
    main()
