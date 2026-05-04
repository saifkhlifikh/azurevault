# AzureVault

## Deployment on Azure VM

1. **Clone the repository:**
   ```bash
   git clone https://github.com/saifkhlifikh/azurevault.git
   cd azurevault
   ```

2. **Setup Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   ```bash
   cp .env.example .env
   nano .env # Add your Azure Blob Storage connection string
   ```

4. **Run Systemd Service:**
   ```bash
   sudo cp azurevault.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now azurevault
   sudo systemctl status azurevault
   ```