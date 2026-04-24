# AIProteinScraper

AIProteinScraper is a Python-based web scraping tool designed to extract and analyze protein-related data from online sources, with support for multiple proxy methods.

## Features

- Automated web scraping of protein-related information
- Multiple request methods: ProxyScrape rotating proxies, Bright Data API, Azure Proxy, Direct Requests
- **True Retrieval-Augmented Generation (RAG)** with vector embeddings (Gemini, OpenAI, or Ollama) and ChromaDB
- Structured JSON extraction with confidence, verdict, evidence, and key fields
- Switchable inference provider: Gemini (free tier), OpenAI API, or local Ollama model
- Interactive Streamlit UI with validation summary, per-source details, and JSON export
- Uses Selenium and BeautifulSoup for data extraction

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/your-username/AIProteinScraper.git
   cd AIProteinScraper
   ```

2. Set up a virtual environment (recommended, Python 3.11 or 3.12):

   ```sh
   # Windows (PowerShell)
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```sh
   python -m pip install -r requirements.txt
   ```

4. Set up environment variables:

   - Copy `sample.env` to `.env`
   - Update it with your credentials based on the chosen method (see Configuration section below)

5. Ensure you have the correct version of `chromedriver` installed and available in the project directory.

## Configuration

This project supports multiple methods for web scraping and inference. Choose the appropriate configuration based on your needs:

### Scraping Method 1: Bright Data API (Default)

For using the Bright Data scraping service:

1. Sign up for a [Bright Data](https://brightdata.com/) account
2. Get your Bright Data Scraping Browser webdriver URL
3. In your `.env` file, set:
   ```
   SBR_WEBDRIVER="your-brightdata-webdriver-url"
   ```

### Scraping Method 2: ProxyScrape (Recommended for Higher Throughput)

For using multiple rotating proxies from your ProxyScrape account:

1. Sign in to your [ProxyScrape dashboard](https://dashboard.proxyscrape.com/v2)
2. Copy either:
   - A full proxy list (recommended), or
   - Single proxy host/port and optional username/password
3. In your `.env` file, set one of the following options:

   Option A: Proxy pool list
   ```
   PROXYSCRAPE_PROXY_LIST="http://user:pass@host1:port1,http://user:pass@host2:port2"
   PROXYSCRAPE_RETRIES="8"
   ```

   Option B: Single endpoint credentials
   ```
   PROXYSCRAPE_SCHEME="http"
   PROXYSCRAPE_HOST="proxy-host"
   PROXYSCRAPE_PORT="proxy-port"
   PROXYSCRAPE_USERNAME="proxy-username"
   PROXYSCRAPE_PASSWORD="proxy-password"
   PROXYSCRAPE_RETRIES="8"
   ```

4. In Streamlit, select `ProxyScrape (rotating proxies)` as scraping method.

### Scraping Method 3: Azure Proxy

For using Azure Virtual Machine as proxy:

1. Set up an Azure VM with a proxy server like Squid
2. In your `.env` file, set:
   ```
   AZURE_PROXY_URL="http://your-azure-vm-ip:proxy-port"
   PROXY_USERNAME="your-proxy-username"  # If authentication is required
   PROXY_PASSWORD="your-proxy-password"  # If authentication is required
   ```

### Scraping Method 4: Direct Requests

For making direct requests without a proxy (use with caution as websites may block your IP):
- No additional configuration needed, but consider using rotating user agents

### Inference Method: Gemini, OpenAI, or Local Ollama

You can choose the provider directly in the Streamlit UI during parsing.

Gemini (free tier — recommended):
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/)
2. In your `.env` file, set:
   ```
   GOOGLE_API_KEY="your-google-api-key"
   GEMINI_MODEL="gemini-2.5-flash"
   ```
3. In Streamlit, choose `Inference provider` = `Gemini (free tier)`.

OpenAI API option:
1. In your `.env` file, set:
   ```
   OPENAI_API_KEY="your-openai-key"
   OPENAI_MODEL="gpt-4o-mini"
   ```
2. In Streamlit, choose `Inference provider` = `OpenAI API`.

Ollama option:
1. [Install Ollama](https://github.com/ollama/ollama) on your machine
2. Start the Ollama service:
   ```sh
   ollama serve
   ```
3. Pull your preferred model:
   ```sh
   ollama pull gemma2:2b
   ```
4. Optional `.env` value:
   ```
   OLLAMA_MODEL="gemma2:2b"
   ```

### Embedding Models for RAG

RAG mode uses **vector embeddings + ChromaDB** for semantic chunk retrieval. The embedding provider is automatically matched to your inference provider selection.

| Provider | Default Embedding Model | Config Variable |
|----------|------------------------|------------------|
| Gemini   | `models/gemini-embedding-001` | `EMBEDDING_MODEL_GEMINI` |
| OpenAI   | `text-embedding-3-small` | `EMBEDDING_MODEL_OPENAI` |
| Ollama   | `nomic-embed-text`       | `EMBEDDING_MODEL_OLLAMA` |

If using Ollama, pull the embedding model first:
```sh
ollama pull nomic-embed-text
```

If embedding fails (e.g. Ollama not running, missing model), the system automatically falls back to keyword-based chunk scoring.

## Usage

1. Start the Streamlit application:

   ```sh
   streamlit run main.py
   ```

2. In the web interface:
   - Enter a protein name
   - Select your preferred scraping method
   - For protein sequence extraction, keep `Follow likely detail pages` enabled and use `Detail pages per source` >= 2
   - Click "Scrape Now" to start the data extraction process
   - Enter any specific parsing instructions in the text area
   - Choose `Inference provider` (`OpenAI API` or `Ollama (local)`)
   - Keep RAG mode enabled for better signal quality on large pages
   - Click "Parse Content" to generate a structured report
   - Review the validation summary table and source-level evidence
   - Download the JSON report for portfolio demos or further analysis

## Common Issues and Troubleshooting

### Connection Error with Ollama
If you see an error like "No connection could be made because the target machine actively refused it":
1. Ensure Ollama is running with `ollama serve`

### Proxy Connection Issues
If you encounter proxy connection problems:
1. Verify your proxy URL is correct
2. Check if your Azure VM firewall allows the connection
3. Try the direct request method as a last resort

## File Structure

- `main.py` - Entry point with Streamlit UI implementation
- `scrape.py` - Handles web scraping logic with multiple methods
- `parse.py` - Parses and structures data using local or cloud LLMs
- `rag_engine.py` - Embedding-based retrieval with ChromaDB vector store
- `protein.py` - Contains protein-specific data functions
- `requirements.txt` - Lists required Python libraries
- `sample.env` - Example environment variables setup

## Additional Features

- **Proxy Support:** The tool supports multiple proxy configurations, including Azure Proxy and Bright Data API, to bypass restrictions and ensure reliable scraping.
- **Proxy Pool Rotation:** ProxyScrape mode rotates across many proxies with retries to improve scraping limits.
- **User-Agent Rotation:** Randomized user-agent headers to reduce the risk of detection.
- **Error Handling:** Comprehensive error handling for robots/proxy/network scraping issues.
- **Session Management:** Streamlit session state is used to manage scraped data efficiently.
- **Embedding-Based RAG:** Semantic vector retrieval using OpenAI or Ollama embeddings with ChromaDB, with graceful fallback to keyword scoring.
- **Portfolio-Friendly Output:** Structured fields (ORGANISM, REFERENCE, AUTHOR, TITLE), confidence, and evidence snippets.

## Future Enhancements

- **Unit Testing:** Add unit tests for all major functions to ensure code reliability.
- **Persistent Vector Store:** Optionally persist ChromaDB collections across sessions for faster re-queries.
- **Cloud Deployment:** Deploy the application on cloud platforms like AWS or Azure for scalability.

## Contribution Guidelines

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes with clear messages.
4. Submit a pull request for review.

For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.

