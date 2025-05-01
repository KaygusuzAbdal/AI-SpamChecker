# 🛡️ AI SpamChecker
AI SpamChecker is a Python-based project that automatically detects and labels spam emails using a machine learning model integrated with the Gmail API. The tool runs in real-time and keeps learning through user feedback, combining classic email security checks (SPF, DKIM, DMARC) with AI-based classification.

## 🚀 Features
 - Real-Time Scanning: Checks your Gmail inbox every 10 seconds.
 - Multi-Language Dataset: Supports both English and Turkish datasets out of the box.
 - SPF, DKIM, DMARC Validation: Includes authentication checks to strengthen spam detection.
 - Self-Learning: Allows user feedback to improve and retrain the model dynamically.
 - Gmail Integration: Uses Gmail API to read, classify, and label your emails.
 - Custom Labeling: Automatically creates and applies 'SPAM' and 'SAFE' labels.

## 🗂️ Project Structure

```
AI-SpamChecker/
├── spam-check.py                # Main script
├── datasets/                    # Contains datasets (English & Turkish)
├── dataset_processor/           # Data normalization module
├── model/                       # Model training & retraining
├── mail_connector/              # Gmail API connector
├── mail_analysis/               # Security checker (SPF/DKIM/DMARC)
├── README.md                    # This file
└── LICENSE
```

## ⚙️ Installation & Setup

1️⃣ Clone the repository:

```
git clone https://github.com/KaygusuzAbdal/AI-SpamChecker.git
cd AI-SpamChecker
```

2️⃣ Install the required dependencies:

```
pip install -r requirements.txt
```

3️⃣ Set up Gmail API credentials:

Follow the Gmail API Quickstart Guide to generate your gmail.json.

Place it under: `mail_connector/credentials/gmail.json`

4️⃣ 📝 Run the project:

```
python spam-check.py
```

## How It Works

The script loads your Gmail inbox and fetches new or unread messages.

For each message:
 - It performs SPF, DKIM, and DMARC validation.
 - It uses a Naive Bayes model (TF-IDF) to predict if the message is spam.
 - If the model is unsure, it prompts you for feedback to retrain and improve.
 - It labels each message as SPAM or SAFE directly in your Gmail inbox.

### Retraining

User feedback is saved into a `local user_feedback_dataset.csv` file.
Whenever new feedback is available, the model automatically retrains to adapt and get smarter over time.

## 🛠️ Tech Stack

Python 3.9+
scikit-learn (TF-IDF + Naive Bayes)
Google Gmail API
Pandas & CSV handling
Regex-based email header analysis

## ✅ To-Do / Improvements
 
 Add unit tests.
 Build a GUI (Tkinter / PyQT).
 Support other email providers (Outlook, Yahoo).
 Add Docker support.

## 📄 License
This project is licensed under the MIT License.
