import requests
import os
import sys
import subprocess
import time
import tempfile
from datetime import datetime

class GitHubUpdater:
    def __init__(self, repo_owner, repo_name, current_version):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version
        self.latest_release = None
        
    def check_for_updates(self):
        """Verifica se há uma nova versão disponível no GitHub"""
        try:
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                tag_name = data.get("tag_name", "").replace("v", "")
                
                # Comparação simples de versão (assumindo formato x.y.z)
                if self._compare_versions(tag_name, self.current_version) > 0:
                    self.latest_release = {
                        "version": tag_name,
                        "url": data.get("html_url"),
                        "assets": data.get("assets", []),
                        "body": data.get("body", "")
                    }
                    return self.latest_release
            return None
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
            return None
            
    def _compare_versions(self, v1, v2):
        """Compara duas versões x.y.z. Retorna 1 se v1 > v2, -1 se v1 < v2, 0 se iguais"""
        try:
            parts1 = [int(p) for p in v1.split(".")]
            parts2 = [int(p) for p in v2.split(".")]
            
            # Padding para garantir mesmo tamanho
            while len(parts1) < 3: parts1.append(0)
            while len(parts2) < 3: parts2.append(0)
            
            if parts1 > parts2: return 1
            if parts1 < parts2: return -1
            return 0
        except:
            return 0
            
    def download_update(self, asset_url, progress_callback=None):
        """Baixa o arquivo de atualização"""
        try:
            response = requests.get(asset_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            # Criar arquivo temporário para o download
            temp_dir = tempfile.gettempdir()
            filename = asset_url.split("/")[-1]
            if not filename.endswith(".exe"):
                filename += ".exe"
                
            download_path = os.path.join(temp_dir, filename)
            
            block_size = 1024 * 8  # 8KB
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = downloaded / total_size
                            progress_callback(progress)
                            
            return download_path
        except Exception as e:
            print(f"Erro no download: {e}")
            return None
            
    def apply_update(self, new_file_path):
        """Aplica a atualização substituindo o executável atual"""
        current_exe = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
        exe_dir = os.path.dirname(current_exe)
        exe_name = os.path.basename(current_exe)
        
        # Script bat para realizar a troca
        # Ele espera o processo atual fechar, move o novo arquivo e reinicia
        bat_script = f"""
@echo off
timeout /t 2 /nobreak > NUL
:loop
tasklist | find "{os.getpid()}" > NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak > NUL
    goto loop
)
move /y "{new_file_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        
        bat_path = os.path.join(tempfile.gettempdir(), "update_script.bat")
        with open(bat_path, "w") as f:
            f.write(bat_script)
            
        # Executar script em background
        subprocess.Popen([bat_path], shell=True)
        sys.exit(0)
