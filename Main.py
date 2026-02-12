import fitz                      # Biblioteca para ler PDFs (PyMuPDF)
import pytesseract              # Biblioteca de OCR (ler texto de imagens)
from PIL import Image, ImageOps # Biblioteca para tratar imagens
import os                       # Biblioteca para lidar com pastas e arquivos
import shutil                   # Biblioteca para mover arquivos
import io                       # Biblioteca para trabalhar com bytes em memória

# Caminho onde o Tesseract está instalado
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Pasta onde estão os PDFs
PASTA_PDFS = "pdfs"

# Pasta onde será salvo o resultado
PASTA_RESULTADO = "resultado"

# Palavra que o usuário quer procurar
PALAVRA_CHAVE = input("Digite a palavra que deseja procurar: ").strip().lower()

# Pastas de saída
PASTA_COM = os.path.join(PASTA_RESULTADO, f"com_{PALAVRA_CHAVE}")   # PDFs que têm a palavra
PASTA_SEM = os.path.join(PASTA_RESULTADO, f"sem_{PALAVRA_CHAVE}")   # PDFs que não têm
PASTA_ERRO = os.path.join(PASTA_RESULTADO, "erro")                 # PDFs com erro

# Cria as pastas caso não existam
for pasta in [PASTA_COM, PASTA_SEM, PASTA_ERRO]:
    os.makedirs(pasta, exist_ok=True)

# Função para melhorar a imagem antes do OCR
def preprocessar_imagem(img: Image.Image) -> Image.Image:
    img = ImageOps.grayscale(img)     # Converte para preto e branco
    img = ImageOps.autocontrast(img)  # Aumenta o contraste
    return img

# Função que verifica se o PDF contém a palavra
def pdf_contem_palavra(caminho_pdf: str, palavra: str) -> bool:
    palavra = palavra.lower()

    try:
        doc = fitz.open(caminho_pdf)  # Abre o PDF

        for pagina in doc:
            # 1) Procura no texto normal do PDF
            texto = pagina.get_text().lower()
            if palavra in texto:
                doc.close()
                return True

            # 2) Procura nas imagens usando OCR
            for img in pagina.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)

                imagem_bytes = base_image.get("image")
                if not imagem_bytes:
                    continue

                try:
                    imagem = Image.open(io.BytesIO(imagem_bytes))  # Abre a imagem
                    imagem = preprocessar_imagem(imagem)          # Trata a imagem

                    texto_ocr = pytesseract.image_to_string(
                        imagem,
                        lang="por+eng",        # Português e inglês
                        config="--psm 6"
                    ).lower()

                    if palavra in texto_ocr:
                        doc.close()
                        return True

                except Exception:
                    continue

        doc.close()
        return False

    except Exception as e:
        print(f"Erro ao analisar {os.path.basename(caminho_pdf)}: {e}")
        return None

# PROCESSAMENTO DOS PDFs
for arquivo in os.listdir(PASTA_PDFS):
    if not arquivo.lower().endswith(".pdf"):
        continue

    caminho_pdf = os.path.join(PASTA_PDFS, arquivo)
    print(f"\nAnalisando: {arquivo}")

    resultado = pdf_contem_palavra(caminho_pdf, PALAVRA_CHAVE)

    if resultado is True:
        shutil.move(caminho_pdf, os.path.join(PASTA_COM, arquivo))
        print(f"Contém a palavra {PALAVRA_CHAVE}")

    elif resultado is False:
        shutil.move(caminho_pdf, os.path.join(PASTA_SEM, arquivo))
        print(f"NÃO contém a palavra {PALAVRA_CHAVE}")

    else:
        shutil.move(caminho_pdf, os.path.join(PASTA_ERRO, arquivo))
        print("Erro ao analisar o PDF")

print("\nAnálise finalizada com sucesso.")
