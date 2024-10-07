#Sample code found in Azure AI Documentation

import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult

endpoint = "https://as-lf-ai-01.cognitiveservices.azure.com/"
key = "18ce006f0ac44579a36bfaf01653254c"

document_intelligence_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

with open("C:/Users/liams/OneDrive/Desktop/Test_Data/Input_Folder/PGCPS-LF-03384/PGCPS-LF-03384_P001.pdf", "rb") as f:
    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-read",
        analyze_request=f,
        output=[AnalyzeOutputOption.PDF],
        content_type="application/octet-stream",
    )
result: AnalyzeResult = poller.result()
operation_id = poller.details["operation_id"]

response = document_intelligence_client.get_analyze_result_pdf(model_id=result.model_id, result_id=operation_id)
with open("analyze_result.pdf", "wb") as writer:
    writer.writelines(response)