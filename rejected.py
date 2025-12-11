import os
import re
import shutil
from datetime import datetime
from PyPDF2 import PdfReader

# --- Configuração de padrões ---
valid_date = r'(20\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])|' \
             r'(0[1-9]|[12]\d|3[01])(0[1-9]|1[0-2])20\d{2})'

valid_patterns = [
    fr'^BR0\d{{8}}-BR-H-6S11-1-{valid_date}[-_]\d{{4}}$',
    fr'^BR0\d{{8}}-BR-H-6S11-1-{valid_date}[-_]\d{{5}}$',
    fr'^BR0\d{{8}}-BR-G-6S11-1-{valid_date}[-_]\d{{4}}$',
    fr'^BR0\d{{8}}-BR-G-6S11-1-{valid_date}[-_]\d{{5}}$',
    fr'^\d{{8}}-\d{{8}}-C\w{{10}}-S-{valid_date}[-_]\d{{4}}$',
    fr'^\d{{8}}-\d{{8}}-C\w{{10}}-S-{valid_date}[-_]\d{{5}}$',
    fr'^\d{{8}}-\d{{8}}-C\w{{10}}-C-{valid_date}[-_]\d{{4}}$',
    fr'^\d{{8}}-\d{{8}}-C\w{{10}}-C-{valid_date}[-_]\d{{5}}$',
    fr'^\d{{8}}-C\w{{10}}-{valid_date}[-_]\d{{4}}$',
    fr'^\d{{8}}-C\w{{10}}-{valid_date}[-_]\d{{5}}$'
]

# Extrai AAAAMMDD (20250131) OU DDMMAAAA (31012025)
date_extract_pattern = re.compile(r'(20\d{6}|\d{2}\d{2}20\d{2})')

# --- Diretórios de destino ---
current_dir = os.getcwd()
invalid_name_dir = os.path.join(current_dir, 'fora_do_padrao')
invalid_pages_dir = os.path.join(current_dir, 'fora_do_limite_paginas')
non_pdf_dir = os.path.join(current_dir, 'fora_do_formato')

# Cria pastas necessárias (se forem usadas depois)
os.makedirs(invalid_name_dir, exist_ok=True)
# invalid_pages_dir e non_pdf_dir serão criadas apenas quando necessário

pages_folder_created = False
non_pdf_folder_created = False

# --- Auxiliares ---


def validar_data(data_str):
    """Tenta validar aaaammdd e ddmmaaaa."""
    formatos = ['%Y%m%d', '%d%m%Y']
    for fmt in formatos:
        try:
            datetime.strptime(data_str, fmt)
            return True
        except ValueError:
            pass
    return False


def is_executable_file(path):
    """
    Detecta executáveis:
    - No Windows: verifica extensão comum de executáveis/script (.exe, .bat, .msi, .cmd, .com, .ps1, .jar, .scr)
    - Em Unix: verifica se o arquivo tem bit de execução.
    """
    if not os.path.isfile(path):
        return False

    # Extensões consideradas executáveis no Windows
    executable_exts = {
        '.exe', '.bat', '.msi', '.com', '.cmd', '.ps1', '.scr', '.jar'
    }
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    if os.name == 'nt':
        return ext in executable_exts
    else:
        # Em sistemas tipo Unix, checar bit executável
        try:
            return os.access(path, os.X_OK)
        except Exception:
            return False


# --- Loop principal ---
for name in os.listdir(current_dir):
    path = os.path.join(current_dir, name)

    # 1) Se for diretório: não mexer
    if os.path.isdir(path):
        # opcional: print(f"⏸️ Ignorado (diretório): {name}")
        continue

    # 2) Se for arquivo executável (não mexer)
    if is_executable_file(path):
        # opcional: print(f"⏸️ Ignorado (executável): {name}")
        continue

    # 3) Se não for PDF (arquivo comum não-executável): mover para 'fora_do_formato'
    if not name.lower().endswith('.pdf'):
        if not non_pdf_folder_created:
            os.makedirs(non_pdf_dir, exist_ok=True)
            non_pdf_folder_created = True
        try:
            destino = os.path.join(non_pdf_dir, name)
            shutil.move(path, destino)
            print(f"🔁 Movido (não-PDF): {name} -> {destino}")
        except Exception as erro:
            print(f"❌ Erro ao mover não-PDF '{name}': {erro}")
        continue

    # 4) Se chegou aqui: é arquivo PDF → validar nome/data/páginas
    name_without_ext = os.path.splitext(name)[0]
    nome_valido = any(re.fullmatch(pat, name_without_ext)
                      for pat in valid_patterns)
    data_valida = False

    if nome_valido:
        match = date_extract_pattern.search(name_without_ext)
        if match:
            if validar_data(match.group(0)):
                data_valida = True
            else:
                print(f"❌ Data inválida no nome: {name}")
        else:
            print(f"❌ Data não encontrada no nome: {name}")
    else:
        print(f"❌ Nome inválido: {name}")

    if not nome_valido or not data_valida:
        try:
            destino = os.path.join(invalid_name_dir, name)
            shutil.move(path, destino)
            print(f"🔁 Movido (nome/data inválidos): {name} -> {destino}")
        except Exception as erro:
            print(f"❌ Erro ao mover '{name}': {erro}")
        continue

    # Ler PDF e contar páginas
    try:
        reader = PdfReader(path)
        num_pages = len(reader.pages)
    except Exception as e:
        print(f"⚠️ Erro ao ler '{name}': {e}")
        try:
            destino = os.path.join(invalid_name_dir, name)
            shutil.move(path, destino)
            print(f"🔁 Movido (erro leitura): {name} -> {destino}")
        except Exception as err2:
            print(f"❌ Erro ao mover após falha de leitura '{name}': {err2}")
        continue

    if num_pages <= 1 or num_pages > 12:
        print(f"❌ '{name}' tem {num_pages} páginas (limite: 2 a 12).")
        if not pages_folder_created:
            os.makedirs(invalid_pages_dir, exist_ok=True)
            pages_folder_created = True
        try:
            destino = os.path.join(invalid_pages_dir, name)
            shutil.move(path, destino)
            print(f"🔁 Movido (páginas fora do limite): {name} -> {destino}")
        except Exception as erro:
            print(f"❌ Erro ao mover '{name}': {erro}")
    else:
        print(f"✅ '{name}' está OK ({num_pages} páginas).")

print("✅ Processo concluído.")
