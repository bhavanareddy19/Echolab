
# --- Embedding and similarity logic for search_similar_b2b_saas_context_by_text ---
import numpy as np
import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel

MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, padding_side='left')
model = AutoModel.from_pretrained(MODEL_ID)

def last_token_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
	left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
	if left_padding:
		return last_hidden_states[:, -1]
	else:
		sequence_lengths = attention_mask.sum(dim=1) - 1
		batch_size = last_hidden_states.shape[0]
		return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]

def get_detailed_instruct(task_description: str, query: str) -> str:
	return f'Instruct: {task_description}\nQuery:{query}'

TASK_DESCRIPTION = 'Given a web search query, retrieve relevant passages that answer the query'

@torch.no_grad()
def embed_query(text: str, max_length=8192) -> np.ndarray:
	formatted_query = get_detailed_instruct(TASK_DESCRIPTION, text)
	batch_dict = tokenizer(
		[formatted_query],
		padding=True,
		truncation=True,
		max_length=max_length,
		return_tensors="pt",
	)
	batch_dict.to(model.device)
	outputs = model(**batch_dict)
	embeddings = last_token_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
	embeddings = F.normalize(embeddings, p=2, dim=1)
	return embeddings[0].cpu().numpy()

def cosine_similarity(vec1, vec2):
	try:
		vec1 = np.array(vec1).flatten()
		vec2 = np.array(vec2).flatten()
		if len(vec1) != len(vec2):
			return 0.0
		similarity = float(np.dot(vec1, vec2))
		similarity = max(-1.0, min(1.0, similarity))
		return similarity
	except Exception:
		return 0.0

async def search_similar_b2b_saas_context_by_text(ticket_text: str, top_k: int = 5):
	q_emb = embed_query(ticket_text)
	records = await get_all_b2b_saas_context()
	all_similarities = []
	for record in records:
		if record.embedding is not None:
			sim = cosine_similarity(q_emb, record.embedding)
			all_similarities.append({
				'record': record,
				'similarity': sim
			})
	all_similarities.sort(key=lambda x: x['similarity'], reverse=True)
	return all_similarities[:top_k]
# Vector similarity search using pgvector (PostgreSQL)
from sqlalchemy import func as sa_func
from app.db import SessionLocal
import numpy as np

async def search_similar_b2b_saas_context(query_embedding, limit=5):
	"""Search for similar records using vector similarity (cosine distance)"""
	async with SessionLocal() as session:
		# Ensure embedding is a list/array of floats
		if isinstance(query_embedding, np.ndarray):
			embedding = query_embedding.tolist()
		else:
			embedding = list(query_embedding)
		result = await session.execute(
			select(B2BSaasContextTable)
			.order_by(B2BSaasContextTable.embedding.cosine_distance(embedding))
			.limit(limit)
		)
		return result.scalars().all()

from sqlalchemy import select
from app.models.b2b_saas_context import B2BSaasContextTable
from app.db import SessionLocal

# Fetch all records
async def get_all_b2b_saas_context():
	async with SessionLocal() as session:
		result = await session.execute(select(B2BSaasContextTable))
		return result.scalars().all()

# Create a new record
defaults = {}
async def create_b2b_saas_context(data_dict):
	async with SessionLocal() as session:
		new_record = B2BSaasContextTable(**data_dict)
		session.add(new_record)
		await session.commit()
		await session.refresh(new_record)
		return new_record

# Get a record by ID
async def get_b2b_saas_context_by_id(record_id):
	async with SessionLocal() as session:
		result = await session.execute(
			select(B2BSaasContextTable).where(B2BSaasContextTable.id == record_id)
		)
		return result.scalar_one_or_none()

