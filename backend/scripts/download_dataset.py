import os
import zipfile
from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import KaggleApi

def main():
    # Load environment variables from .env file
    load_dotenv()
    
    dataset = "solarmainframe/ids-intrusion-csv"
    download_dir = "data/raw/ids-intrusion-csv/"
    
    os.makedirs(download_dir, exist_ok=True)
    
    print(f"Authenticating with Kaggle API...")
    api = KaggleApi()
    api.authenticate()
    
    file_name = "02-14-2018.csv"
    print(f"Downloading file {file_name} from dataset {dataset} to {download_dir}...")
    api.dataset_download_file(dataset, file_name, path=download_dir)
    
    # Check if the file downloaded as a zip and extract if necessary
    zip_path = os.path.join(download_dir, f"{file_name}.zip")
    if os.path.exists(zip_path):
        print(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(download_dir)
        os.remove(zip_path)
    
    print("Download and extraction complete.")

if __name__ == "__main__":
    main()
