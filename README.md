# PDF Downloader Agent

This is an AI agent that downloads PDF files from a webpage in the order you click on them. The agent automatically numbers the downloaded files sequentially (e.g., "1-file_name.pdf", "2-file_name.pdf", etc.).

## Features

- Monitors clicks on PDF icons/links on a webpage
- Downloads files in the exact order you click them
- Automatically numbers files sequentially
- Works specifically with the NIRF rankings webpage

## Requirements

- Python 3.7 or higher
- Chrome browser installed

## Installation

1. Install the required dependencies:

```
pip install -r requirements.txt
```

## Usage

1. Run the PDF downloader agent:

```
python pdf_downloader_agent.py
```

2. The agent will open the NIRF rankings webpage in a Chrome browser
3. Click on any PDF icon on the page to download it
4. Files will be downloaded to the `downloads` folder in the order you click them
5. Press Ctrl+C in the terminal to stop the agent

## How It Works

The agent uses Selenium to:
1. Navigate to the NIRF rankings webpage
2. Set up click event listeners on all PDF links/icons
3. Monitor for clicks and download the PDFs
4. Rename the downloaded files with sequential numbers

## Customization

If you want to use the agent with a different webpage, modify the URL in the `main()` function in `pdf_downloader_agent.py`:

```python
agent.navigate_to_url("your_url_here")
```