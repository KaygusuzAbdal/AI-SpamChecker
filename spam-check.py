
from dataset_processor.dataset_normalizer import DatasetNormalizer
from model.model_trainer.train_model import SpamModelTrainer
from mail_connector.gmail_connector import GmailConnector
from model.model_trainer.model_retrain import retrain_model_from_feedback
import os
import time

CHECK_INTERVAL = 10 # Real-time scan: Every 10 seconds

# Function to create the dataset and train the model (if not already done)
def initialize_and_train_model_if_needed(normalizer, trainer, datasets, master_dataset_path="datasets/master/dataset.csv", model_pkl_path="model/spam_model.pkl"):
    model_exists = os.path.exists(model_pkl_path)  # Path where the model is saved
    # If the model doesn't exist, train and save it for the first time
    if not model_exists:
        print("[*] Model not found, starting training...")
        # If the combined dataset doesn't exist, merge and save it
        if not os.path.exists(master_dataset_path):
            for ds in datasets:
                normalizer.load_dataset(f"datasets/{ds[0]}", ds[1])
            normalizer.save_combined_dataset()
            print("[+] Dataset created and saved.")

        trainer.load_and_clean_dataset()
        trainer.train_model()
        trainer.save_model()
        print("[+] Model successfully trained and saved.")
    else:
        print("[*] Existing model found, loading...")
        trainer.load_model()


def main():
    connector = GmailConnector()
    normalizer = DatasetNormalizer()
    trainer = SpamModelTrainer()

    datasets = [["enron-english-dataset.csv", "en"], ["tr-spam-dataset.csv", "tr"]]

    initialize_and_train_model_if_needed(normalizer, trainer, datasets)

    print("[*] Real-time Spam Check Service is starting...")

    # First run
    first_time = True
    while True:
        if first_time:
            # Fetch all messages (read/unread)
            messages = connector.get_messages(unread=False)
            print(f"[+] All messages checked, total found: ({len(messages)} messages).\n")
            first_time = False
        else:
            # Fetch unread messages without any label
            messages = connector.get_messages(unread=True, exclude_labels=["safe", "spam"])
            print(f"[+] Checking for new messages... ({len(messages)} new messages found).\n")
        # If messages are returned
        if messages != []:
            for msg in messages:
                # Get message details
                details = connector.get_message_detail(msg['id'])
                # Make prediction
                prediction, auth_summary, domain_match, reply_match = trainer.predict_message(details)

                label = 'spam' if prediction else 'safe'

                print(f"Message ID: {details['id']}")
                print(f"From: {details['from']}")
                print(f"Subject: {details['subject']}")
                print(f"auth_results: {auth_summary}")
                print(f"domain_match: {domain_match}")
                print(f"reply_match: {reply_match}")
                print(f"Prediction: {label.upper()}\n")
                
                # If SPF, DKIM, DMARC pass and domain_match + reply_match are true, ask the user for feedback
                if prediction and all(val in auth_summary for val in ['spf:pass', 'dkim:pass', 'dmarc:pass']) and domain_match and reply_match:
                    yanit = input("[?] This email looks safe. Do you think it's SPAM? (y/n): ").strip().lower()
                    if yanit == 'h':
                        label = 'safe'
                        normalizer.save_feedback_to_dataset({
                            'from': details['from'],
                            'subject': details['subject'],
                            'body': details['body'],
                            'spam': False,
                            'spf': 'pass',
                            'dkim': 'pass',
                            'dmarc': 'pass',
                            'reply_match': reply_match
                        })
                        print("[+] User feedback saved, retraining the model...")
                        retrain_model_from_feedback()

                connector.add_message_label(msg['id'], label)
        print("\n") if first_time else time.sleep(CHECK_INTERVAL)


# Run this function if spam-check.py is executed directly
if __name__ == '__main__':
    main()
