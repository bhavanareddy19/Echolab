# scrape_embed_store.py
from dotenv import load_dotenv
import os
import time
import nodriver as uc
import asyncio
from curl_cffi import requests
import re

load_dotenv()

# Replace the embedding section completely:
import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel

print("🚀 Loading local model...")
MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"

# Official implementation
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, padding_side='left')
model = AutoModel.from_pretrained(MODEL_ID)
print("✅ Model loaded successfully!")

def last_token_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    """Official implementation from Qwen model card"""
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

@torch.no_grad()
def embed_texts(texts, max_length=8192):
    """
    Document embedding for chunks (NO instruction for docs).
    Official Qwen implementation - CORRECTED VERSION
    """
    # Documents don't need instruction formatting - just raw text
    batch_dict = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    batch_dict.to(model.device)
    
    # Get embeddings
    outputs = model(**batch_dict)
    embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
    
    # Normalize
    embeddings = F.normalize(embeddings, p=2, dim=1)
    
    return embeddings.cpu().numpy()

def calculate_text_confidence(text: str) -> float:
    """Calculate confidence score based on text quality metrics"""
    if not text or len(text.strip()) == 0:
        return 0.0
    
    length_score = min(len(text) / 500, 1.0)
    words = text.split()
    word_count_score = min(len(words) / 50, 1.0)
    unique_chars = len(set(text.lower()))
    char_diversity_score = min(unique_chars / 30, 1.0)
    sentence_markers = len(re.findall(r'[.!?]', text))
    sentence_score = min(sentence_markers / 3, 1.0)
    alphanumeric_chars = sum(1 for c in text if c.isalnum())
    alphanumeric_ratio = alphanumeric_chars / len(text) if len(text) > 0 else 0
    
    confidence = (
        length_score * 0.3 +
        word_count_score * 0.2 +
        char_diversity_score * 0.2 +
        sentence_score * 0.15 +
        alphanumeric_ratio * 0.15
    )
    return round(confidence, 3)

def get_embedding_local_with_confidence(text: str):
    """Get embedding using corrected Qwen implementation + confidence score"""
    vec = embed_texts([text])[0]
    confidence_score = calculate_text_confidence(text)
    return vec.tolist(), confidence_score

def get_embedding_local(text: str):
    """Get embedding using corrected Qwen implementation"""
    vec = embed_texts([text])[0]
    return vec.tolist()

def split_into_chunks_by_tokens(text, max_tokens=350, overlap_tokens=45):
    """
    Split by tokens with overlap. Uses tokenizer to count tokens.
    Keeps sentence boundaries by default decode; good enough and simple.
    """
    chunks = []
    # Note: add_special_tokens=False to avoid repeated BOS/EOS across chunks
    tokens = tokenizer.encode(text, add_special_tokens=False)
    step = max_tokens - overlap_tokens
    for i in range(0, len(tokens), step):
        chunk_tokens = tokens[i:i+max_tokens]
        if not chunk_tokens:
            continue
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        if chunk_text.strip():
            chunks.append(chunk_text.strip())
    return chunks

async def extract_text_from_site(link):
    """Extract text from a website using nodriver to bypass blockers"""
    browser = None
    try:
        print(f"🌐 Starting browser for: {link}")
        browser = await uc.start(
            headless=True,
            browser_args=[
                '--no-first-run',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--allow-running-insecure-content'
            ]
        )
        print("📄 Navigating to page...")
        page = await browser.get(link)

        print("⏳ Waiting for page to load...")
        await asyncio.sleep(5)

        try:
            await page.wait_for(selector='body', timeout=10)
        except:
            print("⚠️ Body selector timeout, continuing anyway...")

        print("📝 Extracting page content...")

        try:
            content_selectors = [
                'main','article','[role="main"]','.content','.post',
                '.entry','.post-content','.article-content','#content',
                '.main-content','.page-content'
            ]
            for selector in content_selectors:
                try:
                    element = await page.select(selector)
                    if element:
                        raw_text = await element.get_text()
                        if raw_text and len(raw_text.strip()) > 100:
                            cleaned_text = clean_extracted_text(raw_text)
                            print(f"✅ Extracted {len(cleaned_text)} characters using selector: {selector}")
                            return cleaned_text
                except:
                    continue

            print("⚠️ No content found with main selectors, trying paragraphs...")
            paragraphs = await page.select_all('p')
            if paragraphs:
                all_text = []
                for p in paragraphs:
                    try:
                        p_text = await p.get_text()
                        if p_text and len(p_text.strip()) > 20:
                            all_text.append(p_text.strip())
                    except:
                        continue
                if all_text:
                    combined_text = ' '.join(all_text)
                    cleaned_text = clean_extracted_text(combined_text)
                    print(f"✅ Extracted {len(cleaned_text)} characters from {len(all_text)} paragraphs")
                    return cleaned_text
        except Exception as e:
            print(f"⚠️ Improved DOM extraction failed: {e}")

        try:
            js_script = """
            const unwantedSelectors = [
              'script','style','nav','header','footer',
              '.nav','.header','.footer','.sidebar','.ads',
              '.advertisement','.social','.share','.comment',
              '.comments','.related','.recommended','#comments',
              '.menu','.navigation','.breadcrumb','.pagination'
            ];
            unwantedSelectors.forEach(s => document.querySelectorAll(s).forEach(el => el.remove()));
            const contentSelectors = [
              'main','article','[role="main"]','.content','.post','.entry',
              '.post-content','.article-content','#content','.main-content','.page-content'
            ];
            for (let selector of contentSelectors) {
              const el = document.querySelector(selector);
              if (el) {
                const text = el.innerText || el.textContent;
                if (text && text.trim().length > 500) return text.trim();
              }
            }
            const paragraphs = document.querySelectorAll('p');
            let content = '';
            paragraphs.forEach(p => {
              const t = p.innerText || p.textContent;
              if (t && t.trim().length > 20) content += t.trim() + ' ';
            });
            return content.trim();
            """
            raw_text = await page.evaluate(js_script)
            if raw_text and len(raw_text.strip()) > 100:
                cleaned_text = clean_extracted_text(raw_text)
                print(f"✅ Extracted {len(cleaned_text)} characters using enhanced JavaScript extraction")
                return cleaned_text
        except Exception as e:
            print(f"⚠️ Enhanced JavaScript extraction failed: {e}")

        try:
            html_content = await page.get_content()
            if html_content:
                print("⚠️ Using aggressive HTML parsing fallback...")
                unwanted_patterns = [
                    r'<script[^>]*>.*?</script>',
                    r'<style[^>]*>.*?</style>',
                    r'<nav[^>]*>.*?</nav>',
                    r'<header[^>]*>.*?</header>',
                    r'<footer[^>]*>.*?</footer>',
                    r'<aside[^>]*>.*?</aside>',
                    r'<div[^>]*class="[^"]*(?:nav|menu|sidebar|ads|social|comment)[^"]*"[^>]*>.*?</div>',
                ]
                text_content = html_content
                for pattern in unwanted_patterns:
                    text_content = re.sub(pattern, '', text_content, flags=re.DOTALL | re.IGNORECASE)
                main_content_patterns = [
                    r'<main[^>]*>(.*?)</main>',
                    r'<article[^>]*>(.*?)</article>',
                    r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
                    r'<div[^>]*id="content"[^>]*>(.*?)</div>',
                ]
                main_content = ""
                for pattern in main_content_patterns:
                    matches = re.findall(pattern, text_content, flags=re.DOTALL | re.IGNORECASE)
                    if matches:
                        main_content = matches[0]
                        break
                if not main_content or len(main_content.strip()) < 500:
                    paragraph_matches = re.findall(r'<p[^>]*>(.*?)</p>', text_content, flags=re.DOTALL | re.IGNORECASE)
                    main_content = ' '.join(paragraph_matches)
                text_content = re.sub(r'<[^>]+>', '', main_content)
                text_content = re.sub(r'\s+', ' ', text_content)
                if text_content and len(text_content.strip()) > 100:
                    cleaned_text = clean_extracted_text(text_content)
                    print(f"✅ Extracted {len(cleaned_text)} characters using aggressive HTML parsing")
                    return cleaned_text
        except Exception as e:
            print(f"⚠️ Aggressive HTML parsing failed: {e}")

        print("❌ All extraction methods failed")
        return ""
    except Exception as e:
        print(f"❌ Error extracting from {link}: {e}")
        return ""
    finally:
        if browser:
            try:
                await browser.quit()
                print("🔒 Browser closed")
            except:
                pass

def clean_extracted_text(text):
    """Enhanced cleaning for extracted text"""
    if not text:
        return ""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if (line and len(line) > 10 and 
            not line.lower().startswith(('menu','nav','home','about','contact','login','sign up','search')) and
            not line.lower() in ['', ' ', '\t', '\n']):
            cleaned_lines.append(line)
    cleaned_text = ' '.join(cleaned_lines)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = re.sub(r'(cookie|privacy policy|terms of service|subscribe|newsletter)', '', cleaned_text, flags=re.IGNORECASE)
    return cleaned_text.strip()

async def main_from_url(url):
    """URL in -> cleaned text -> chunks -> embeddings (+confidence)"""
    print(f"🌐 Processing URL: {url}")
    text = await extract_text_from_site(url)
    if not text:
        print("❌ Failed to extract content from URL")
        return []
    print(f"📝 Extracted text length: {len(text)} characters")

    print("✂️ Splitting into chunks...")
    chunks = split_into_chunks_by_tokens(text, max_tokens=350, overlap_tokens=45)
    print(f"📄 Created {len(chunks)} chunks")

    embeddings_with_confidence = []
    for i, chunk in enumerate(chunks):
        print(f"⏳ Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
        try:
            embedding, confidence = get_embedding_local_with_confidence(chunk)
            embeddings_with_confidence.append({
                'embedding': embedding,
                'confidence': confidence,
                'chunk_text': chunk,
                'chunk_length': len(chunk),
                'word_count': len(chunk.split())
            })
            print(f"✅ Got embedding (dim: {len(embedding)}, confidence: {confidence:.3f})")
        except Exception as e:
            print(f"❌ Error processing chunk {i+1}: {e}")
        if (i + 1) % 10 == 0:
            print(f"📊 Progress: {i+1}/{len(chunks)} chunks completed")

    print(f"\n🎉 Successfully generated {len(embeddings_with_confidence)} embeddings!")
    if embeddings_with_confidence:
        avg_conf = sum(item['confidence'] for item in embeddings_with_confidence) / len(embeddings_with_confidence)
        print(f"📊 Average confidence score: {avg_conf:.3f}")
    return embeddings_with_confidence

def main(text):
    """Original function for processing text directly (no scraping)"""
    print("✂️ Splitting into chunks...")
    chunks = split_into_chunks_by_tokens(text, max_tokens=350, overlap_tokens=45)
    print(f"📄 Created {len(chunks)} chunks")
    embeddings = []
    for i, chunk in enumerate(chunks):
        print(f"⏳ Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
        try:
            embedding = get_embedding_local(chunk)
            embeddings.append(embedding)
            print(f"✅ Got embedding of dimension: {len(embedding)}")
        except Exception as e:
            print(f"❌ Error processing chunk {i+1}: {e}")
        if (i + 1) % 10 == 0:
            print(f"📊 Progress: {i+1}/{len(chunks)} chunks completed")
    print(f"\n🎉 Successfully generated {len(embeddings)} embeddings!")
    if embeddings:
        print(f"📊 Sample embedding (first 5 values): {embeddings[0][:5]}")
    return embeddings

def process_url(url):
    """Sync wrapper"""
    return asyncio.run(main_from_url(url))
