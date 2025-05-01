import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score
from mail_analysis.security_checker import EmailSecurityChecker
import joblib

class SpamModelTrainer:
    def __init__(self, dataset_path="datasets/master/dataset.csv"):
        self.dataset_path = dataset_path  # dataset to be used
        self.df = None
        self.model = None
        self.vectorizer = None # We will convert text data to numerical vectors and store it here

    # Loads the saved model and vectorizer from disk
    def load_model(self, model_dir="model", model_name="spam_model"):
        model_path = os.path.join(model_dir, f"{model_name}.pkl")
        vectorizer_path = os.path.join(model_dir, f"{model_name}_tfidf_vectorizer.pkl")

        if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
            print(f"[!] Model or vectorizer file not found: {model_path}")
            return

        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)
        print("[+] Model and vectorizer loaded successfully.\n")

    # Function to load and clean the dataset
    def load_and_clean_dataset(self):
        if not os.path.exists(self.dataset_path):
            print(f"[!] Error: Dataset not found: {self.dataset_path}")
            return

        df = pd.read_csv(self.dataset_path) # load the dataset
        df.dropna(subset=['body', 'spam'], inplace=True) # remove rows with missing 'body' or 'spam' data
        df['body'] = df['body'].astype(str) # convert 'body' content to string

        if 'subject' in df.columns:
            df['subject'] = df['subject'].astype(str) # if 'subject' exists, convert to string

        if 'from' in df.columns:
            df['from'] = df['from'].astype(str) # if 'from' exists, convert to string

        self.df = df # save the cleaned dataset
        print(f"[+] {len(df)} records loaded and cleaned.")

    # function to train the model
    def train_model(self):
        # combine 'from', 'subject', and 'body' fields to learn from all (if any field is missing, it's taken as empty string)
        # axis=1 => row
        self.df['combined'] = self.df.apply(
            lambda row: f"{row.get('from', '')} {row.get('subject', '')} {row.get('body', '')}", axis=1
        )

        X = self.df['body'] # email content as feature
        y = self.df['spam'] # spam label as target

        # split the data: 80% training, 20% testing
        # random_state=42 -> ensures the same split every time
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # convert text data to numerical vectors (TF-IDF: Term Frequency - Inverse Document Frequency)
        self.vectorizer = TfidfVectorizer()
        X_train_tfidf = self.vectorizer.fit_transform(X_train) # learn word weights from training data
        X_test_tfidf = self.vectorizer.transform(X_test) # transform test data using the same model

        # train the model using MultinomialNB for text classification
        # https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.MultinomialNB.html
        self.model = MultinomialNB()
        self.model.fit(X_train_tfidf, y_train)

        # predict on test data to evaluate performance
        y_pred = self.model.predict(X_test_tfidf)

        metrics = classification_report(y_test, y_pred)
        accuracy = f"{accuracy_score(y_test, y_pred):.4f}"

        print("[+] Model Performance Report:\n" + metrics)
        print(f"Accuracy: {accuracy}")

    # function to save the trained model and vectorizer
    def save_model(self, output_dir="model", model_name="spam_model"):
        os.makedirs(output_dir, exist_ok=True)  # create folder if it doesn't exist
        joblib.dump(self.model, os.path.join(output_dir, f"{model_name}.pkl"))  # save model
        joblib.dump(self.vectorizer, os.path.join(output_dir, f"{model_name}_tfidf_vectorizer.pkl"))  # save vectorizer
        print(f"[+] Model and vectorizer saved to the '{output_dir}' folder.")

    # function to make predictions with external text data
    def predict_message(self, message_details):
        if self.model is None or self.vectorizer is None:
            print("[!] Model or vectorizer is not loaded.")
            return None

        # extract required fields from headers
        from_field = message_details['from']
        subject = message_details['subject']
        body = message_details['body']

        # combine 'from', 'subject', and 'body' for prediction
        combined_text = f"{from_field} {subject} {body}"

        # get DKIM, SPF, DMARC and other security results
        checker = EmailSecurityChecker(message_details)
        auth_summary = checker.extract_auth_summary()
        domain_match = checker.check_domain_match()
        reply_match = checker.check_reply_to_match()

        # convert text to numerical vector and predict
        transformed = self.vectorizer.transform([combined_text])
        prediction = self.model.predict(transformed)

        #extra_signals = f"{auth_summary} domainmatch:{domain_match} replymatch:{reply_match}"
        #combined_text = f"{message_details['from']} {message_details['subject']} {message_details['body']} {extra_signals}"
        #vectorized_text = self.vectorizer.transform([combined_text])
        #prediction = self.model.predict(vectorized_text)

        return bool(prediction[0]), auth_summary, domain_match, reply_match


# Example usage:
# print(trainer.predict_message(
#     from_field="noreply@google.com",
#     subject="Güvenlik uyarısı",
#     body="Oturum açma engellendi",
#     auth_results="spf=pass dkim=pass dmarc=pass"
# ))
