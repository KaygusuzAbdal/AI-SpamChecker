import pandas as pd
from model.model_trainer.train_model import SpamModelTrainer
import os

def retrain_model_from_feedback():
    # read user feedback file and merge it into the main dataset
    # define paths as constants/static variables
    FEEDBACK_PATH = "datasets/user_feedback_dataset.csv"
    MASTER_DATASET_PATH = "datasets/master/dataset.csv"

    # merge if the feedback file exists
    if os.path.exists(FEEDBACK_PATH):
        print("[+] Feedback data found. Integrating into the main dataset...")

        # read feedback data
        feedback_df = pd.read_csv(FEEDBACK_PATH)

        # read the main dataset
        master_df = pd.read_csv(MASTER_DATASET_PATH)

        # fill missing columns if any
        for col in ['from', 'subject', 'body', 'spam']:
            if col not in feedback_df.columns:
                feedback_df[col] = ''
            if col not in master_df.columns:
                master_df[col] = ''

        # combine the datasets
        combined_df = pd.concat([master_df, feedback_df], ignore_index=True) # ignore_index=True ->  resets the index
        combined_df.drop_duplicates(subset=['from', 'subject', 'body'], inplace=True) # inplace=True -> modifies in memory

        # save as the new master dataset
        combined_df.to_csv(MASTER_DATASET_PATH, index=False) # index=False prevents saving the index column
        print(f"[+] New dataset saved: {MASTER_DATASET_PATH} (with {len(combined_df)} records)\n")

        # delete the feedback file
        os.remove(FEEDBACK_PATH)
        print("[+] Feedback file has been cleared.\n")
    else:
        print("[!] No new feedback data found. Existing model will continue to be used.\n")

    # retrain the model
    trainer = SpamModelTrainer()
    trainer.load_and_clean_dataset()
    trainer.train_model()
    trainer.save_model()
    print("[+] Model successfully retrained!")
