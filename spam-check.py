
from dataset_processor.dataset_normalizer import DatasetNormalizer
from model.model_trainer.train_model import SpamModelTrainer
from mail_connector.gmail_connector import GmailConnector
from model.model_trainer.model_retrain import retrain_model_from_feedback
import os
import time

CHECK_INTERVAL = 10 # Real-Time taraması: 10 saniye

# dataset oluşturma ve model eğitme fonksiyonu (eğer daha önce oluşturulmadıysa)
def initialize_and_train_model_if_needed(normalizer, trainer, datasets, master_dataset_path="datasets/master/dataset.csv", model_pkl_path="model/spam_model.pkl"):
    model_exists = os.path.exists(model_pkl_path)  # modelin kaydedildiği yer
    # Model yoksa sadece ilk kez çalıştır ve kaydet
    if not model_exists:
        print("[*] Model bulunamadı, eğitiliyor...")
        # Dataset yoksa sadece ilk kez birleştir ve kaydet
        if not os.path.exists(master_dataset_path):
            for ds in datasets:
                normalizer.load_dataset(f"datasets/{ds[0]}", ds[1])
            normalizer.save_combined_dataset()
            print("[+] Dataset oluşturuldu ve kaydedildi.")

        trainer.load_and_clean_dataset()
        trainer.train_model()
        trainer.save_model()
        print("[+] Model başarıyla eğitildi ve kaydedildi.")
    else:
        print("[*] Kayıtlı model bulundu, yükleniyor...")
        trainer.load_model()


def main():
    connector = GmailConnector()
    normalizer = DatasetNormalizer()
    trainer = SpamModelTrainer()

    datasets = [["enron-english-dataset.csv", "en"], ["tr-spam-dataset.csv", "tr"]]

    initialize_and_train_model_if_needed(normalizer, trainer, datasets)

    print("[*] Real-time Spam Check Servisi Başlatılıyor...")

    # ilk kez çalışıyorsa
    first_time = True
    while True:
        if first_time:
            # okunmuş/okunmamış tüm mesajları getir
            messages = connector.get_messages(unread=False)
            print(f"[+] Tüm mesajlar kontrol edildi, toplam ({len(messages)} mesaj bulundu).\n")
            first_time = False
        else:
            # okunmamış ve etiketi olmayan mesajları getir
            messages = connector.get_messages(unread=True, exclude_labels=["safe", "spam"])
            print(f"[+] Yeni mesajlar kontrol ediliyor... ({len(messages)} yeni mesaj bulundu).\n")
        # eğer veri döndüyse
        if messages != []:
            for msg in messages:
                # mesaj detaylarını getir
                details = connector.get_message_detail(msg['id'])
                # Tahmin yap
                prediction, auth_summary, domain_match, reply_match = trainer.predict_message(details)

                label = 'spam' if prediction else 'safe'

                print(f"Message ID: {details['id']}")
                print(f"From: {details['from']}")
                print(f"Subject: {details['subject']}")
                print(f"auth_results: {auth_summary}")
                print(f"domain_match: {domain_match}")
                print(f"reply_match: {reply_match}")
                print(f"Prediction: {label.upper()}\n")
                
                # SPF, DKIM, DMARC domain_match ve reply_match değerleri true dönerse, kullanıcıya sor:
                if prediction and all(val in auth_summary for val in ['spf:pass', 'dkim:pass', 'dmarc:pass']) and domain_match and reply_match:
                    yanit = input("[?] Bu mail güvenli görünüyor. Sence gerçekten SPAM mı? (e/h): ").strip().lower()
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
                        print("[+] Kullanıcı geri bildirimi kaydedildi, model yeniden eğitiliyor...")
                        retrain_model_from_feedback()

                connector.add_message_label(msg['id'], label)
        print("\n") if first_time else time.sleep(CHECK_INTERVAL)


# eğer spam-check.py dosyası DOĞRUDAN çalıştırılıyorsa bu fonksiyonu çalıştır
if __name__ == '__main__':
    main()
