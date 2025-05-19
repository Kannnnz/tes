"""
Script untuk menguji kemampuan model dalam menjawab pertanyaan tentang konteks
dokumen dan Universitas Negeri Semarang (UNNES). Script ini berguna untuk
fine-tuning dan evaluasi model dalam konteks aplikasi Document Summarizer.
"""

import argparse
import httpx
import os
import time
import json
from text_extractor import extract_text

# Default API endpoint
DEFAULT_API_ENDPOINT = "http://127.0.0.1:1234"
DEFAULT_MODEL = "mistral-nemo-instruct-2407"

# UNNES-specific prompts
UNNES_TEST_QUESTIONS = [
    "Ceritakan sejarah singkat Universitas Negeri Semarang.",
    "Apa saja fakultas yang ada di UNNES?",
    "Berapa jumlah program studi di UNNES?",
    "Siapa rektor UNNES saat ini?",
    "Dimana lokasi kampus utama UNNES?",
    "Apa visi dan misi UNNES?",
    "Apa saja prestasi UNNES dalam 5 tahun terakhir?",
    "Bagaimana profil lulusan UNNES?",
    "Apa saja kegiatan penelitian unggulan di UNNES?",
    "Jelaskan tentang sistem penerimaan mahasiswa baru di UNNES."
]

# Paper analysis prompts
PAPER_TEST_QUESTIONS = [
    "Siapa penulis paper ini dan kapan diterbitkan?",
    "Apa judul lengkap dari paper ini?",
    "Apa metode penelitian yang digunakan dalam paper ini?",
    "Apa hasil utama yang ditemukan dalam penelitian ini?",
    "Apa kesimpulan dari paper ini?",
    "Apa saja batasan atau limitasi dalam penelitian ini?",
    "Apa kontribusi utama yang diberikan oleh paper ini?",
    "Jelaskan metodologi yang digunakan dalam penelitian ini.",
    "Bagaimana desain eksperimen dalam paper ini?",
    "Apa saran untuk penelitian selanjutnya berdasarkan paper ini?"
]

# Non-relevant questions (should be filtered by our backend)
IRRELEVANT_TEST_QUESTIONS = [
    "Bagaimana cara membuat kue coklat?",
    "Siapa presiden Amerika Serikat saat ini?",
    "Berapa harga bitcoin hari ini?",
    "Apa film terbaru yang sedang tayang di bioskop?",
    "Bagaimana cara main gitar?"
]

def test_model_on_document(document_path, questions, system_prompt=None, temperature=0.7, endpoint=DEFAULT_API_ENDPOINT, model=DEFAULT_MODEL):
    """
    Test model responses on a document with specific questions
    
    Args:
        document_path (str): Path to document file
        questions (list): List of questions to ask
        system_prompt (str): Optional system prompt
        temperature (float): Temperature parameter for generation
        endpoint (str): API endpoint URL
        model (str): Model identifier
    """
    
    # Extract document text
    print(f"Extracting text from {document_path}...")
    document_text = extract_text(document_path)
    document_name = os.path.basename(document_path)
    
    print(f"\nDocument: {document_name}")
    print(f"Text length: {len(document_text)} characters")
    
    # Run tests for each question
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n[{i}/{len(questions)}] Testing question: {question}")
        
        # Build context + question prompt
        prompt = f"""Berikut adalah konten dari dokumen '{document_name}':

{document_text[:10000]}  # Batasi untuk menghindari konteks yang terlalu panjang

Pertanyaan: {question}

Berikan jawaban yang informatif dan akurat berdasarkan konten dokumen di atas."""

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request data
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000
        }
        
        # Send request to API
        try:
            start_time = time.time()
            response = httpx.post(
                f"{endpoint}/v1/chat/completions",
                json=data,
                timeout=60.0
            )
            end_time = time.time()
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                response_text = result["choices"][0]["message"]["content"]
                
                # Print timing information
                print(f"Response time: {end_time - start_time:.2f} seconds")
                
                # Print truncated response
                max_preview = 300
                preview = response_text[:max_preview] + ("..." if len(response_text) > max_preview else "")
                print(f"Response preview: {preview}")
                
                # Save result
                results.append({
                    "question": question,
                    "response": response_text,
                    "response_time": end_time - start_time
                })
            else:
                print(f"Error: API returned status code {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"Exception when calling LM Studio API: {e}")
    
    # Save results to file
    output_file = f"test_results_{os.path.splitext(document_name)[0]}_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nTest results saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Test model responses on documents')
    parser.add_argument('document', help='Path to document file')
    parser.add_argument('--type', choices=['paper', 'unnes', 'irrelevant', 'custom'], default='paper', 
                        help='Type of questions to test')
    parser.add_argument('--custom-questions', help='Path to JSON file with custom questions')
    parser.add_argument('--system', default="Kamu adalah asisten AI yang fokus pada paper penelitian dan Universitas Negeri Semarang (UNNES).",
                        help='System prompt')
    parser.add_argument('--temperature', type=float, default=0.7, help='Temperature for generation')
    parser.add_argument('--endpoint', default=DEFAULT_API_ENDPOINT, help='LM Studio API endpoint')
    parser.add_argument('--model', default=DEFAULT_MODEL, help='Model identifier')
    
    args = parser.parse_args()
    
    # Select question set based on type
    if args.type == 'paper':
        questions = PAPER_TEST_QUESTIONS
    elif args.type == 'unnes':
        questions = UNNES_TEST_QUESTIONS
    elif args.type == 'irrelevant':
        questions = IRRELEVANT_TEST_QUESTIONS
    elif args.type == 'custom':
        if not args.custom_questions:
            print("Error: --custom-questions file path required for custom question type")
            return
        try:
            with open(args.custom_questions, 'r', encoding='utf-8') as f:
                questions = json.load(f)
                if not isinstance(questions, list):
                    print("Error: Custom questions file must contain a JSON array of strings")
                    return
        except Exception as e:
            print(f"Error loading custom questions: {e}")
            return
    
    # Run tests
    test_model_on_document(
        document_path=args.document,
        questions=questions,
        system_prompt=args.system,
        temperature=args.temperature,
        endpoint=args.endpoint,
        model=args.model
    )

if __name__ == "__main__":
    main()