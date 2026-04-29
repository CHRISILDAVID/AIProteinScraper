# ProtScrape: AI-Powered Protein Data Scraper 🧬

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online-brightgreen?logo=azure)](https://protscrape.icyrock-1df5a8cd.eastus.azurecontainerapps.io/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-ff4b4b?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Azure Container Apps](https://img.shields.io/badge/Azure-Container%20Apps-0078d4?logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/en-us/products/container-apps/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-4b7bec)](https://www.trychroma.com/)
[![Selenium](https://img.shields.io/badge/Selenium-Browser%20Automation-43b02a?logo=selenium&logoColor=white)](https://www.selenium.dev/)
[![LangChain](https://img.shields.io/badge/LangChain-RAG%20Pipeline-2f7df6)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-LLM-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![Gemini](https://img.shields.io/badge/Gemini-LLM-1a73e8?logo=google&logoColor=white)](https://aistudio.google.com/)

**A unified platform for biological data retrieval, featuring both a high-performance REST API engine and a traditional DOM web scraping showcase.**

ProtScrape is a modern Python tool that retrieves protein information from major biological databases. It integrates a ChromaDB vector store using RAG (Retrieval-Augmented Generation) and uses large language models (LLMs) to extract structured fields — with **full source attribution** for every piece of information.

The application allows you to toggle seamlessly between two distinct engines:
1. **API-Based Engine (ProtScrapeAPI)**: A high-performance, concurrent engine querying 6 major databases directly via their native REST APIs.
2. **DOM-Based Engine**: A legacy web scraping showcase that demonstrates traditional browser automation, proxy rotation, and HTML parsing techniques.

---

## Key Features

### API-Based Engine (Recommended)
- **API-First Architecture** — Queries [UniProt](https://www.uniprot.org/), [PDB](https://www.rcsb.org/), [NCBI Protein](https://www.ncbi.nlm.nih.gov/protein/), [InterPro](https://www.ebi.ac.uk/interpro/), [KEGG](https://www.genome.jp/kegg/), and [STRING](https://string-db.org/) via their native REST APIs.
- **Concurrent Fetching** — All databases queried in parallel for rapid retrieval (~5 seconds total).
- **Native JSON Parsing** — Direct, clean data retrieval bypassing CAPTCHAs and anti-bot measures.

### DOM-Based Engine (Showcase)
- **Proxy Support** — Built-in rotation for ProxyScrape, Bright Data API, and Azure Proxy.
- **Automated Web Scraping** — Browser simulation using Selenium and BeautifulSoup4.
- **Detail Page Follow** — Automatically follows biological database detail pages to aggregate context.

### Shared Capabilities
- **RAG Pipeline** — [ChromaDB](https://www.trychroma.com/) vector store with semantic embeddings for intelligent context retrieval.
- **Multi-Provider LLM** — Supports [Gemini](https://aistudio.google.com/) (free tier), [OpenAI](https://platform.openai.com/), and [Ollama](https://github.com/ollama/ollama) (local).
- **Source Attribution** — Every extracted field is linked to its exact database source.
- **Premium UI** — Streamlit UI with a unified dark theme, glassmorphism, and gradient accents.
- **Data Export** — Download structured JSON reports and CSV field tables.

---

## Installation

1. Clone the repository and navigate to the project directory:
   ```sh
   git clone https://github.com/your-username/AIProteinScraper.git
   cd AIProteinScraper
   ```

2. Create a virtual environment (Python 3.11+ recommended):
   ```sh
   # Windows (PowerShell)
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install all unified dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```sh
   cp sample.env .env
   ```
   *Edit `.env` with your API keys based on the Configuration section below.*

5. Ensure you have the correct version of `chromedriver` installed and available in the project directory if you plan to use the DOM-based engine.

---

## Configuration

### LLM Inference Methods

**Gemini (recommended — free tier)**
1. Get a free API key from [Google AI Studio](https://aistudio.google.com/).
2. In `.env`:
   ```env
   GOOGLE_API_KEY="your-google-api-key"
   GEMINI_MODEL="gemini-2.5-flash"
   ```

**OpenAI API (optional)**
```env
OPENAI_API_KEY="your-openai-key"
OPENAI_MODEL="gpt-4o-mini"
```

**Ollama (local — optional)**
```sh
# Start Ollama service and pull models
ollama serve
ollama pull gemma2:2b
ollama pull nomic-embed-text  # Used for RAG embeddings
```

### Scraping Proxies (DOM-Based Engine Only)
The DOM engine supports several proxy backends if direct requests are failing:
- **ProxyScrape**: Provide a proxy pool list in `PROXYSCRAPE_PROXY_LIST`.
- **Bright Data API**: Add your webdriver URL to `SBR_WEBDRIVER`.
- **Azure Proxy**: Add VM details to `AZURE_PROXY_URL`, `PROXY_USERNAME`, and `PROXY_PASSWORD`.

---

## Usage

1. Start the unified Streamlit application:
   ```sh
   streamlit run main.py
   ```

2. **Select your Engine**: In the left sidebar, choose between **ProtScrape (API-Based)** and **ProtScrape (DOM-Based)**.

3. **Running the Pipeline**:
   - **Protein Name**: Enter a target (e.g., *hemoglobin*, *insulin*, *p53*).
   - **Configuration**: Select your data sources (or scraping methods), LLM provider, and RAG top-K chunk settings.
   - **Execution**: Click **"Analyze Protein"** (or **"Scrape Now"** followed by **"Parse Content"**).
   - **Results**: Review the validation summary tables, source-level evidence, and download the aggregated JSON/CSV report.

---

## Container Deployment (Azure Container Apps)

The included Dockerfile bundles headless Chromium for the DOM engine. The app listens on `$PORT` (default `8000`).

### Local Docker
```sh
docker build -t protscrape:latest .
docker run --rm -p 8000:8000 --env-file .env protscrape:latest
```

### Azure (Portal)
1. Create an Azure Container Registry (ACR) and push the image.
2. Create an Azure Container App using that image.
3. Set **Ingress** to **External** and **Target Port** to `8000`.
4. Add environment variables from your `.env` (e.g., `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `SBR_WEBDRIVER`, proxy settings).
5. Restart the app and use the Application URL as your live demo link.

---

## Embedding Models for RAG

RAG mode uses **vector embeddings + ChromaDB** for semantic chunk retrieval. The embedding provider is automatically matched to your inference provider selection.

| Provider        | Default Embedding Model             | Config Variable                     |
|-----------------|-------------------------------------|-------------------------------------|
| Gemini          | `models/gemini-embedding-001`       | `EMBEDDING_MODEL_GEMINI`            |
| OpenAI          | `text-embedding-3-small`            | `EMBEDDING_MODEL_OPENAI`            |
| Ollama          | `nomic-embed-text`                  | `EMBEDDING_MODEL_OLLAMA`            |

*If embedding fails (e.g., Ollama not running), the system automatically falls back to keyword-based chunk scoring.*

---

## Architecture

```text
AIProteinScraper/
├── main.py                 # Unified Streamlit entry point (Toggles API vs DOM)
├── config.py               # Shared environment variables logic
├── ProtScrapeAPI/          # High-performance REST API Engine
│   ├── sources/            # Individual database fetchers (UniProt, PDB, etc.)
│   ├── engine/             # RAG Pipeline (Chunking, ChromaDB, LLM, Prompts)
│   └── ui/                 # Glassmorphism Theme and Sidebar
├── scrape.py               # Legacy DOM Engine web scraping logic
├── parse.py                # Legacy DOM Engine Ollama/LLM parsing
├── rag_engine.py           # Legacy DOM Engine RAG backend
├── protein.py              # Legacy DOM Engine search URL generation
└── .env                    # Shared configuration keys
```

## License

This project is licensed under the MIT License.
