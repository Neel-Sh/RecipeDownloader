# 🍳 Recipe Downloader

**Recipe Downloader** is a sleek, open-source web app that turns any recipe URL into an interactive cooking checklist. Built with Flask and modern JavaScript, it helps you cook with confidence — track your progress, scale your ingredients, and even listen to step-by-step voice instructions.

---

## ✨ Features

- 🔗 Paste a recipe URL and extract ingredients + instructions
- ✅ Interactive checkboxes to track your cooking progress
- 🔊 Built-in voice assistant (Text-to-Speech) for steps
- 🎚️ Adjust ingredient amounts based on servings
- 💾 Local progress saved via browser memory
- 🌓 Light & Dark Mode toggle
- 🔒 No login required — runs fully in-browser

---

## 📦 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Neel-Sh/RecipeDownloader.git
cd RecipeDownloader
```

### 2. Create and activate a virtual environment (optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
flask run
```

Then open your browser to:  
📍 `http://127.0.0.1:5000`

---

## 🛠 Built With

- **Python** + **Flask** – backend web server
- **HTML5/CSS3 + JS** – responsive front-end
- **SpeechSynthesis API** – voice-guided cooking
- **LocalStorage** – remembers progress without logins

---

## 📂 Project Structure

```
RecipeDownloader/
├── static/
│   ├── css/           # Stylesheets
│   └── js/            # Client-side JS
├── templates/         # HTML templates
├── app.py             # Flask backend (assumed)
├── requirements.txt   # Python dependencies
└── README.md
```

---

## 🧪 Example Recipe URLs

Try one of these:

- https://www.allrecipes.com/recipe/229960/quick-chicken-piccata/
- https://www.bbcgoodfood.com/recipes/perfect-pancakes-recipe

---

## 🧑‍💻 Contributing

Pull requests are welcome! Please open an issue first to discuss what you’d like to change.

---


## Acknowledgements

- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing

---

 🌐 [@neel_sh_](https://twitter.com/neel_sh_)
