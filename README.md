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
├── spam-check.py                   # Main script to run the spam checker
├── datasets/                       # Contains datasets and dataset README (English & Turkish)
│   ├── enron-english-dataset.csv   # (Download required; see README.txt)
│   ├── tr-spam-dataset.csv         # Turkish dataset
│   └── README.txt                  # Dataset usage & download instructions
├── dataset_processor/              # Data normalization module
│   └── dataset_normalizer.py
├── model/                          # Model training & retraining
│   └── model_trainer/
│       ├── train_model.py
│       └── model_retrain.py
├── mail_connector/                 # Gmail API connector
│   ├── gmail_connector.py
│   └── credentials/
│       └── gmail.json              # Gmail API credentials (not included)
├── mail_analysis/                  # Security checker (SPF/DKIM/DMARC)
│   └── security_checker.py
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
└── LICENSE                         # License file
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

For each mail:
 - It performs SPF, DKIM, and DMARC validation.
 - It uses a Naive Bayes model (TF-IDF) to predict if the message is spam.
 - If the model is unsure, it prompts you for feedback to retrain and improve.
 - It labels each message as SPAM or SAFE directly in your Gmail inbox.

### Retraining

User feedback is saved into a `local user_feedback_dataset.csv` file.
Whenever new feedback is available, the model automatically retrains to adapt and get smarter over time.

## 🛠️ Tech Stack

Python 3.9+ , scikit-learn (TF-IDF + Naive Bayes) , Google Gmail API , Pandas & CSV handling , Regex-based email header analysis

## ✅ To-Do / Improvements
 
 - Add unit tests.
 - Build a GUI (Tkinter / PyQT).
 - Support other email providers (Outlook, Yahoo).
 - Add Docker support.

## 📄 License
This project is licensed under the MIT License.
