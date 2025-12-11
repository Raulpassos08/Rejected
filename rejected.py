import os
import re
import shutil
from datetime import datetime
from PyPDF2 import PdfReader

# Regex para data válida em aaaammdd ou ddmmaaaa
valid_date = r'(20\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])|' \
             r'(0[1-9]|[12]\d|3[01])(0[1-9]|1[0-2])20\d{2})'

# Padrões válidos com data sintaticamente correta
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

# Extrai qualquer sequência de 8 números começando com 20
date_extract_pattern = re.compile(r'20\d{6}')

# Diretórios principais
current_dir = os.getcwd()
invalid_name_dir = os.path.join(current_dir, 'fora_do_padrao')
invalid_pages_dir = os.path.join(current_dir, 'fora_do_limite_paginas')

# Criados quando necessários
os.makedirs(invalid_name_dir, exist_ok=True)
pages_folder_created = False

# Função para validar data nos 2 formatos


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


# Loop principal
for filename in os.listdir(current_dir):

    filepath = os.path.join(current_dir, filename)

    # Ignorar pastas e não-PDF sem mover
    if not os.path.isfile(filepath):
        continue

    if not filename.lower().endswith('.pdf'):
        print(f"⏭️ Ignorado (não é PDF): {filename}")
        continue

    # A partir daqui, é PDF válido para análise
    name_without_ext = os.path.splitext(filename)[0]
    nome_valido = any(re.fullmatch(pattern, name_without_ext)
                      for pattern in valid_patterns)

    data_valida = False

    if nome_valido:
        match = date_extract_pattern.search(name_without_ext)
        if match:
            if validar_data(match.group(0)):
                data_valida = True
            else:
                print(f"❌ Data inválida no nome: {filename}")
        else:
            print(f"❌ Data não encontrada no nome: {filename}")
    else:
        print(f"❌ Nome inválido: {filename}")

    # Nome ou data inválida → mover
    if not nome_valido or not data_valida:
        try:
            destino = os.path.join(invalid_name_dir, filename)
            shutil.move(filepath, destino)
            print(f"🔁 Movido para: {destino}\n")
        except Exception as erro:
            print(f"❌ Erro ao mover '{filename}': {erro}\n")
        continue

    # Verifica páginas
    try:
        reader = PdfReader(filepath)
        num_pages = len(reader.pages)
    except Exception as e:
        print(f"⚠️ Erro ao ler '{filename}': {e}")
        destino = os.path.join(invalid_name_dir, filename)
        shutil.move(filepath, destino)
        continue

    if num_pages <= 1 or num_pages > 12:
        print(f"❌ '{filename}' tem {num_pages} páginas (limite: 2 a 12).")
        if not pages_folder_created:
            os.makedirs(invalid_pages_dir, exist_ok=True)
            pages_folder_created = True
        destino = os.path.join(invalid_pages_dir, filename)
        shutil.move(filepath, destino)
        print(f"🔁 Movido para: {destino}\n")
    else:
        print(f"✅ '{filename}' está OK ({num_pages} páginas).\n")

print("✅ Processo concluído.")
