<h1 align="center">Welcome to AI-Web-Search-Agent 👋</h1>
<p>
</p>

The AI Web Search Agent is a tool designed to automate data retrieval and extraction tasks by leveraging web search capabilities.
Given a dataset (in CSV or Google Sheets format), the AI agent reads specific entities in a chosen column, performs web searches for each, and uses a language model (LLM) to parse relevant information based on user-defined queries. The structured output can then be viewed in a simple dashboard interface and downloaded for further analysis and also added to the google sheet.



## Setup Guide

```sh
1. Clone the repository.
2. Python version used is 3.11
3. Run pip install requirements.txt
4. Get your SERP API KEY AND GROQ API KEY and add them in config.json
5. Create your OAuth 2.0 Client credentials and download them as client_secret.json file from google cloud console, alSo enable to Google Sheet API.
6. Run the application by -> streamlit run app.py

```

## Usage Guide

```sh
1. Chose the file format you want to upload.
2. If you are under CSV Tab- upload a csv file or If under Google sheet Tab- upload the sheet link.
3. For uploading the google sheet link, authorize your google account by signing in
4. After uploading the file or sheet, you will see the data preview and data statistics.
5. Select the main column for which you want to query from droplist list of column names.
6. For writing the template make sure you use the chose main column name in curly braces in the query.
7. If the query entered is in correct format then valid template message is shown and query preview is shown.
8. Execute web search and LLM processing by clicking on the "exectue web search" button.
9. The results show the desired information along with the confidence score, the web sources and brief notes.
10. You can see the analysis tab and also download the data in csv file, or add data to google sheet- if input was google sheet.


```

## Additional features

```sh
1. Setting up database with name search_results.db using sqlite to cache the search results
2. Provide users information about validation success and errors (if any) regarding failed API calls or LLM queries.
3. Added google sheet output intergation by making a new sheet in the link
4. We can ask for multiple info in the query template providing advanced query searches.

```
