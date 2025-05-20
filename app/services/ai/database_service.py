from dotenv import load_dotenv
import os, boto3, openai, tempfile, time, shutil
from botocore.exceptions import ClientError
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.embeddings import OpenAIEmbeddings

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET")

if not all([openai.api_key, AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, S3_BUCKET]):
    raise ValueError("Missing required environment variables for OpenAI or AWS.")

S3_PREFIX= ""
CHROMA_PATH = "chroma"

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

def load_documents():
    documents = []
    
    try:
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
        for page in page_iterator:
            if "Contents" not in page:
                print("Không tìm thấy file trong S3 bucket.")
                continue
            for obj in page["Contents"]:
                key = obj["Key"]
                if key.endswith("/"):
                    continue

                suffix = os.path.splitext(key)[1]
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, f"temp_{os.urandom(8).hex()}{suffix}")
                
                try:
                    # print(f"Đang tải file từ S3: {key}")
                    s3.download_file(S3_BUCKET, key, temp_file_path)
                    
                    if key.lower().endswith(".pdf"):
                        loader = UnstructuredPDFLoader(temp_file_path, mode="single")
                    elif key.lower().endswith(".docx"):
                        loader = UnstructuredWordDocumentLoader(temp_file_path, mode="single")
                    elif key.lower().endswith((".md", ".txt")):
                        loader = TextLoader(temp_file_path, encoding="utf-8")
                    else:
                        print(f"Bỏ qua file không hỗ trợ: {key}")
                        continue

                    try:
                        docs = loader.load()
                        documents.extend(docs)
                        # print(f"Đã tải {len(docs)} tài liệu từ {key} (S3).")
                    except Exception as e:
                        print(f"Lỗi khi tải tài liệu từ {key}: {e}")
                    
                except ClientError as e:
                    print(f"Lỗi khi tải file S3 {key}: {e}")
                except Exception as e:
                    print(f"Lỗi xử lý {key}: {e}")
                finally:
                    for _ in range(3):
                        try:
                            if os.path.exists(temp_file_path):
                                os.unlink(temp_file_path)
                            break
                        except PermissionError as e:
                            print(f"Không thể xóa {temp_file_path}: {e}")
                            time.sleep(0.2)
                    else:
                        print(f"Không thể xóa {temp_file_path} sau nhiều lần thử.")

    except ClientError as e:
        print(f"Lỗi khi liệt kê đối tượng S3: {e}")
        raise

    # print(f"Tổng cộng tải được {len(documents)} tài liệu từ S3.")
    return documents

def split_text(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    # print(f"Chia {len(documents)} tài liệu thành {len(chunks)} đoạn.")
    
    return chunks

def save_to_chroma(chunks: list[Document]):
    # print(f"Xóa cơ sở dữ liệu Chroma cũ nếu tồn tại tại {CHROMA_PATH}...")
    # if os.path.exists(CHROMA_PATH):
    #     try:
    #         shutil.rmtree(CHROMA_PATH)
    #         print(f"Đã xóa thư mục {CHROMA_PATH}.")
    #     except Exception as e:
    #         print(f"Lỗi khi xóa thư mục {CHROMA_PATH}: {e}")
    #         raise

    try:
        db = Chroma.from_documents(
            chunks, OpenAIEmbeddings(), persist_directory=CHROMA_PATH
        )
        # print(f"Đã lưu {len(chunks)} đoạn vào {CHROMA_PATH}.")
    except Exception as e:
        print(f"Lỗi khi tạo cơ sở dữ liệu Chroma: {e}")
        raise

def generate_data_store():
    documents = load_documents()
    if not documents:
        print("Không có tài liệu nào được tải từ S3. Kết thúc quá trình.")
        return
    chunks = split_text(documents)
    if not chunks:
        print("Không có đoạn nào được tạo. Kết thúc quá trình.")
        return
    save_to_chroma(chunks)

def main():
    generate_data_store()

if __name__ == "__main__":
    main()