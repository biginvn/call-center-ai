import argparse, os, openai, shutil, warnings, time
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from database_service import generate_data_store

# Tải biến môi trường
load_dotenv()
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Kiểm tra biến môi trường
required_env_vars = ["OPENAI_API_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Thiếu các biến môi trường: {missing_vars}")

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Trả lời câu hỏi dựa chỉ trên ngữ cảnh sau:

{context}

---

Trả lời câu hỏi dựa trên ngữ cảnh trên: {question}
"""

def main():
    parser = argparse.ArgumentParser(description="Truy vấn cơ sở dữ liệu Chroma với câu hỏi.")
    parser.add_argument("query_text", type=str, help="Câu hỏi cần truy vấn.")
    args = parser.parse_args()

    query_text = args.query_text

    total_start = time.time()

    # Check hoặc tạo database
    if not os.path.exists(CHROMA_PATH):
        print("Không tìm thấy database, đang tạo mới...")
        generate_data_store()

    # Khởi tạo embedding và database
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Check số lượng documents
    doc_count = db._collection.count()
    if doc_count == 0:
        print("Database rỗng.")
        return

    # Tìm kiếm tài liệu
    search_start = time.time()
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    search_time = time.time() - search_start

    if not results or results[0][1] < 0.7:
        print("Không tìm thấy kết quả phù hợp.")
        return

    # Tạo prompt
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # Gọi GPT-4o
    model = ChatOpenAI(model_name="gpt-4o")
    gpt_start = time.time()
    response = model.invoke(prompt)
    gpt_time = time.time() - gpt_start

    # Định dạng phản hồi
    response_text = response.content
    sources = [doc.metadata.get("source", "Không rõ nguồn") for doc, _ in results]
    formatted_response = f"Phản hồi: {response_text}\nNguồn: {sources}"
    print(formatted_response)

    total_time = time.time() - total_start

    print(f"\n⏱️ Thời gian tìm kiếm: {search_time:.2f}s | GPT: {gpt_time:.2f}s | Tổng: {total_time:.2f}s")

if __name__ == "__main__":
    main()
