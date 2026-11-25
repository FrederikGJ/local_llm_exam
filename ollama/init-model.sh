#!/bin/sh
# Henter OLLAMA_MODEL og laver en alias-model (LLM_ALIAS) med vores parametre,
# så RAG-appen altid kan kalde den samme modelnavn uanset hvilken model der ligger bag.
# Henter også embeddingmodellen (EMBED_MODEL), som RAG-indekseringen bruger.
set -eu

echo "Henter model: ${OLLAMA_MODEL}"
ollama pull "${OLLAMA_MODEL}"

echo "Henter embeddingmodel: ${EMBED_MODEL}"
ollama pull "${EMBED_MODEL}"

cat > /tmp/Modelfile <<EOF
FROM ${OLLAMA_MODEL}
PARAMETER temperature ${LLM_TEMPERATURE}
PARAMETER num_ctx ${LLM_NUM_CTX}
EOF

echo "Opretter ${LLM_ALIAS} (FROM ${OLLAMA_MODEL}, temperature=${LLM_TEMPERATURE}, num_ctx=${LLM_NUM_CTX})"
ollama create "${LLM_ALIAS}" -f /tmp/Modelfile

ollama list
echo "Klar: ${LLM_ALIAS} -> ${OLLAMA_MODEL}, embeddings: ${EMBED_MODEL}"
