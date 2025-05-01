import pandas as pd
import os
from datetime import datetime
import random
import csv

class DatasetNormalizer:
    def __init__(self):
        self.datasets = []

    # function to load the dataset and analyze its structure
    # takes dataset file path and language as arguments
    def load_dataset(self, filepath, lang):
        filename = os.path.basename(filepath) # get the file name
        ext = os.path.splitext(filename)[1].lower() # get the file extension

        if ext == '.csv':
            df = pd.read_csv(filepath, encoding='utf-8', sep=None, engine='python', on_bad_lines='skip')
        else:
            raise ValueError(f"This file format is not supported: {ext}") # stop if unsupported (no .tsv handling for now)

        df = self._normalize(df, lang)
        self.datasets.append(df)

    # private function to normalize datasets into a unified structure
    def _normalize(self, df, lang):
        # columns to create
        columns = ['from', 'subject', 'body', 'date', 'spam', 'language']
        new_df = pd.DataFrame(columns=columns) # create a new dataset with these columns

        df_columns = [col.lower() for col in df.columns] # convert all column names to lowercase to avoid errors

        # Match Body
        # look for a column that likely contains the email body (searching for body, text, or message; skip if it contains 'id')
        body_col = next((col for col in df_columns if ('body' in col or 'text' in col or 'message' in col) and 'id' not in col), None)
        if body_col:
            new_df['body'] = df[df.columns[df_columns.index(body_col)]]  # if found, copy to the new dataset
        else:
            new_df['body'] = [None] * len(df)

        # Match Subject
        # look for a column that likely contains the email subject (searching for subject field)
        subject_col = next((col for col in df_columns if 'subject' in col), None)
        if subject_col:
            new_df['subject'] = df[df.columns[df_columns.index(subject_col)]] # copy if found
        else:
            # if not found, use the first sentence (up to '.') of the body or first 80 characters as a fallback
            new_df['subject'] = new_df['body'].apply(lambda x: str(x).split('.')[0][:80] if pd.notnull(x) else None)

        # Match From
        # look for a column that likely contains the sender (searching for sender and from fields)
        from_col = next((col for col in df_columns if 'from' in col or 'sender' in col), None)
        if from_col:
            new_df['from'] = df[df.columns[df_columns.index(from_col)]] # copy if found
        else:
            new_df['from'] = ['noreply@example.com'] * len(df) # default if not found

        # Date eşleştirme
        # look for a column that likely contains the date (searching for timestamp and sender fields)
        date_col = next((col for col in df_columns if 'date' in col or 'timestamp' in col), None)
        if date_col:
            date_series = df[df.columns[df_columns.index(date_col)]] # copy if found
            new_df['date'] = pd.to_datetime(date_series, errors='coerce').dt.strftime('%Y-%m-%d')
        else:
            # if date column not found, generate a random date between 2015-2024
            new_df['date'] = [datetime(random.randint(2015, 2024), random.randint(1, 12), random.randint(1, 28)).strftime('%Y-%m-%d') for _ in range(len(df))]

        # Match Label
        # look for a column that likely contains the label (spam info) (searching for label, class and spam fields)
        label_col = next((col for col in df_columns if 'label' in col or 'class' in col or 'spam' in col), None)
        if label_col:
            # If the column is found:
            # If the column value is "spam", "1", "true", or "yes", set it to True (these are categorized as spam)
            # If the column value is different, set it to False (these are not categorized as spam)
             new_df['spam'] = df[df.columns[df_columns.index(label_col)]].apply(
                lambda x: True if str(x).lower().strip() in ['spam', '1', '1.0', 'true', 'yes'] else False
            )
        else:
            new_df['spam'] = [None] * len(df) # set as "None" if not found

        # add language
        new_df['language'] = lang.lower()

        return new_df
    
    # save new feedback data to CSV
    def save_feedback_to_dataset(self, row, file_path="datasets/user_feedback_dataset.csv"):
        fieldnames = ['from', 'subject', 'body', 'spam', 'spf', 'dkim', 'dmarc', 'reply_match']
        file_exists = os.path.isfile(file_path)

        with open(file_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    
    # combine all datasets
    def get_combined_dataset(self):
        return pd.concat(self.datasets, ignore_index=True)
    
    # (Optional) save combined dataset to disk if we want to work on a saved file instead of keeping it in memory
    def save_combined_dataset(self, output_dir="datasets/master", file_name="dataset.csv"):
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, file_name)
        combined_df = self.get_combined_dataset()

        # if file already exists, merge with existing data
        if os.path.exists(output_path):
            try:
                existing_df = pd.read_csv(output_path)
                combined_df = pd.concat([existing_df, combined_df], ignore_index=True)
                combined_df.drop_duplicates(inplace=True)
                print("[+] Merged with existing dataset, duplicates removed.")
            except Exception as e:
                print(f"[!] Warning: Existing dataset could not be read. Continuing with new data. Error: {e}")

        combined_df.to_csv(output_path, index=False)
        print(f"[+] Dataset saved: {output_path}")
