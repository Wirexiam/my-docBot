from docxtpl import DocxTemplate
import subprocess
import os


def create_docx_from_data(template_name: str, context: dict, user_path: str):
    # Загружаем шаблон
    doc = DocxTemplate(f"./templates/{template_name}.docx")

    # Данные для подстановки
    # Рендерим документ
    doc.render(context)

    # Сохраняем результат
    doc.save(f"{user_path}/{template_name}.docx")
    return f"{user_path}/{template_name}.docx"


def convert_docx_to_pdf_libreoffice(input_docx_path, user_path=None):
    """
    Converts a DOCX file to a PDF using the LibreOffice command line.

    Args:
        input_docx_path (str): The path to the input .docx file.
        output_dir (str, optional): The directory where the PDF will be saved.
                                    If None, the PDF will be saved in the
                                    same directory as the input file.
    """
    if not os.path.exists(input_docx_path):
        print(f"Error: The file '{input_docx_path}' does not exist.")
        return

    if user_path is None:
        user_path = os.path.dirname(input_docx_path)

    # The command to run LibreOffice in headless mode
    command = [
        "libreoffice",
        "--convert-to",
        "pdf",
        "--outdir",
        user_path,
        input_docx_path,
    ]

    try:
        # Run the command and capture output
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Successfully converted '{input_docx_path}' to PDF in '{user_path}'.")
    except FileNotFoundError:
        print(
            "Error: LibreOffice executable not found. Please ensure it's installed and in your PATH."
        )
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during conversion:")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")


def create_user_doc(user_path, template_name, context):
    user_path_docx = create_docx_from_data(
        template_name=template_name,
        context=context,
        user_path=user_path,
    )
    print(f"{user_path_docx}------------")
    convert_docx_to_pdf_libreoffice(input_docx_path=user_path_docx, user_path=user_path)
    return user_path_docx


# create_user_doc(
#     "/home/johngoworks/projects/pdf_generator", "template_ready", {"full_name": "Nastya"}
# )
