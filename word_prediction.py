from transformers import BertTokenizer, BertForMaskedLM
import torch
from nltk.stem import WordNetLemmatizer
import nltk
import spacy
from nltk.data import find

def download_wordnet_if_needed():
    try:
        # Try to find wordnet locally
        find('corpora/wordnet.zip')
        print("WordNet is already downloaded.")
    except LookupError:
        # If not found, download it
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)
        print("Downloaded WordNet.")

# Call this function instead of downloading every time
download_wordnet_if_needed()

# Load pre-trained BERT model and tokenizer
model_name = "bert-base-uncased"
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForMaskedLM.from_pretrained(model_name)

# Initialize lemmatizer and SpaCy model for NER
lemmatizer = WordNetLemmatizer()
nlp = spacy.load("en_core_web_sm")

def is_proper_noun_or_entity(word):
    """
    Check if a word is a proper noun or entity using SpaCy.
    """
    doc = nlp(word)
    for token in doc:
        if token.pos_ == "PROPN" or token.ent_type_:
            return True
    return False

def predict_with_bert(context, prefix, max_suggestions=10):
    """
    Predict contextual word completions using BERT.
    `context` is the full sentence up to the word being typed.
    `prefix` is the current fragment of the word.
    """
    input_text = f"{context} {prefix}[MASK]"
    input_ids = tokenizer.encode(input_text, return_tensors="pt")

    # Predict the masked token
    outputs = model(input_ids)
    logits = outputs.logits

    # Locate the [MASK] token in the input
    mask_token_index = torch.where(input_ids == tokenizer.mask_token_id)[1]
    mask_logits = logits[0, mask_token_index, :]

    # Convert logits to probabilities
    probabilities = torch.softmax(mask_logits, dim=1)

    # Get all tokens and filter by prefix
    all_tokens = tokenizer.get_vocab()
    matching_tokens = {
        token: probabilities[0, token_id].item()
        for token, token_id in all_tokens.items()
        if token.startswith(prefix)
    }

    # Sort by probability
    sorted_tokens = sorted(matching_tokens.items(), key=lambda x: x[1], reverse=True)

    # Filter proper nouns, entities, and refine suggestions
    suggestions = []
    for token, _ in sorted_tokens:
        if not is_proper_noun_or_entity(token):
            if token.startswith("##") or token in tokenizer.all_special_tokens:
                continue
            if not token.startswith(prefix):
                continue
            # suggestions.append(token)
            decoded = tokenizer.convert_tokens_to_string([token]).strip()
            if not is_proper_noun_or_entity(decoded) and decoded not in suggestions:
                suggestions.append(decoded)
            if len(suggestions) == max_suggestions:
                break

    return suggestions
