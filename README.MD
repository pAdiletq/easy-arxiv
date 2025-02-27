# EasyArxiv

EasyArxiv is a web application designed to simplify the process of searching, reading, and learning from research papers on arXiv. It provides an intuitive interface for users to search for papers, view statistics, and engage in interactive learning through AI-generated flashcards and quizzes.

## Features

- **Search Papers**: Quickly search for research papers by topic.
- **View Statistics**: Visualize publication trends with interactive charts.
- **AI Quest**: Engage in an interactive learning journey with AI-generated flashcards and quizzes.
- **Text-to-Speech**: Listen to paper summaries using TTS.
- **PDF Links**: Access full-text PDFs of research papers.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/silvermete0r/easy-arxiv.git
    cd easy-arxiv
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```
    
3. Create a `config.json` file in the /static/data/ directory and add your ORCID credentials:
```
{
    "orcid_client_id": "your_client_id_here",
    "redirect_uri": "your_redirect_uri_here"
}
```
⚠️ Make sure the file is located at /static/data/config.json so the application can load it properly.

4. Configure the `.env` file with your API keys:
    ```
    GOOGLE_API_KEY=your_google_api_key_here
    ```
    ```
    CLIENT_ID = your_client_id_here
    ```
    ```
    CLIENT_SECRET = your_client_secret_here
    ```
    ```
    REDIRECT_URI = your_redirect_uri_here

    ```

5. Run the application:
    ```sh
    python app.py
    ```

## Usage

1. Open your web browser and navigate to `http://127.0.0.1:5000`.
2. Use the search bar to find research papers by topic.
3. Click on the "AI Quest" button to start an interactive learning session for a selected paper.
4. View publication statistics on the homepage.

## Project Structure

- **static/**: Contains static files such as CSS, JavaScript, and HTML templates.
- **templates/**: Contains HTML templates for rendering web pages.
- **app.py**: Main application file that sets up the FastAPI server and routes.
- **requirements.txt**: Lists the Python dependencies required for the project.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## Acknowledgements

- [arXiv](https://arxiv.org/) for providing access to a vast repository of research papers.
- [Tailwind CSS](https://tailwindcss.com/) for the beautiful UI components.
- [Chart.js](https://www.chartjs.org/) for the interactive charts.
- [Font Awesome](https://fontawesome.com/) for the icons.