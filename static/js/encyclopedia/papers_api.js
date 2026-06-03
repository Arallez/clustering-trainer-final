/**
 * Scientific papers API client.
 * The browser receives already ranked recommendations from Django; ontology
 * context, source fetching, scoring and caching live on the backend.
 */

export async function fetchScientificPapers(apiUrl, totalLimit = 20) {
    const url = new URL(apiUrl, window.location.origin);
    url.searchParams.set('limit', String(totalLimit));

    const response = await fetch(url.toString(), {
        headers: {
            'Accept': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error(`Articles API failed with HTTP ${response.status}`);
    }

    const payload = await response.json();
    return {
        articles: payload.articles || [],
        profile: payload.profile || null,
        concept: payload.concept || null
    };
}
