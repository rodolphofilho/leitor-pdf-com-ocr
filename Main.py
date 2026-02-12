import fitz 
import pytesseract
from PIL import Image, ImageOps
import os
import shutil
import io


os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


PASTA_PDFS = "pdfs"
PASTA_RESULTADO = "resultado"
PALAVRA_CHAVE = input("Digite a palavra que deseja procurar: ").strip().lower()

PASTA_COM = os.path.join(PASTA_RESULTADO, f"com_{PALAVRA_CHAVE}")
PASTA_SEM = os.path.join(PASTA_RESULTADO, f"sem_{PALAVRA_CHAVE}")
PASTA_ERRO = os.path.join(PASTA_RESULTADO, "erro")


for pasta in [PASTA_COM, PASTA_SEM, PASTA_ERRO]:
    os.makedirs(pasta, exist_ok=True)


def preprocessar_imagem(img: Image.Image) -> Image.Image:
    
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    return img


def pdf_contem_palavra(caminho_pdf: str, palavra: str) -> bool:
    palavra = palavra.lower()

    try:
        doc = fitz.open(caminho_pdf)

        for pagina in doc:
            # TEXTO NATIVO DO PDF 
            texto = pagina.get_text().lower()
            if palavra in texto:
                doc.close()
                return True

            # OCR EM IMAGENS 
            for img in pagina.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)

                imagem_bytes = base_image.get("image")
                if not imagem_bytes:
                    continue

                try:
                    imagem = Image.open(io.BytesIO(imagem_bytes))
                    imagem = preprocessar_imagem(imagem)

                    texto_ocr = pytesseract.image_to_string(
                        imagem,
                        lang="por+eng",
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
        print(f"Erro ao analisar{os.path.basename(caminho_pdf)}: {e}")
        return None


# PROCESSAMENTO DOS PDF
for arquivo in os.listdir(PASTA_PDFS):
    if not arquivo.lower().endswith(".pdf"):
        continue

    caminho_pdf = os.path.join(PASTA_PDFS, arquivo)
    print(f"\nAnalisando:{arquivo}")

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
