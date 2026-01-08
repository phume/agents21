// Simple regex-based extractor for demo purposes.
// In a real production environment, this should be replaced by an LLM or a specialized NER model.

const extract = (text) => {
    const entities = [];

    if (!text) return entities;

    // Regex to find things that look like names or organizations (capitalized words)
    // This is VERY naive and will produce false positives.
    // Ideally, we'd use something like Compromise.js or an API call to OpenAI.

    // Example: Looking for patterns like "John Doe" or "Acme Corp"
    // Excluding common start words

    const potentialMatches = text.match(/[A-Z][a-z]+(?:\s[A-Z][a-z]+)+/g) || [];

    const uniqueMatches = [...new Set(potentialMatches)];

    uniqueMatches.forEach(match => {
        // Simple filter to trash some obviously common phrases that aren't entities
        const ignore = ['Press Release', 'Department', 'Justice', 'United States', 'New York', 'Washington'];
        let keep = true;
        for (const ig of ignore) {
            if (match.includes(ig)) keep = false;
        }

        if (keep) {
            entities.push({
                name: match,
                type: 'Person/Org' // Generic type for now
            });
        }
    });

    return entities;
};

module.exports = { extract };
